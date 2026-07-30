import os
print("\n\n" + "="*50)
print("  EXECUTING NICEGUI_APP.PY (NOT STREAMLIT)")
print("="*50 + "\n\n")
import asyncio
import re
import sys
import webbrowser
import logging
import ipaddress

from dataclasses import dataclass, field

from datetime import datetime

from pathlib import Path

from typing import Any, Dict, Optional, List
from urllib.parse import urlparse

from nicegui import app, run, ui
from starlette.responses import JSONResponse
from html_sanitizer import Sanitizer

from seo_aio_engine import SEOAIOAnalyzer, ScrapeBlockedError
from core.safe_fetch import UnsafeURLError, ContentTooLargeError, TooManyRedirectsError
from core.ui.panels import (
    bind_panel_dependencies,
    report_panel,
    render_saved_run_workspace,
    results_panel,
)
from core.application import (
    build_token_usage_text,
    execute_competitor_analysis,
    execute_primary_analysis,
    export_detailed_docx_report,
    export_detailed_markdown_report,
    export_history_csv,
    export_priority_actions_csv,
    load_saved_run_bundle,
    persist_analysis_run,
)
from core.config import config
from core.storage.database import get_history
from core.ui.dashboard import (
    build_history_rows,
    render_history_table,
)
from shared.billing.api import router as phase2_billing_router
from shared.billing.webhook_handler import router as stripe_webhook_router
from shared.auth.nicegui_auth import NiceGUIAuthMiddleware
from shared.usage.api import router as usage_router
from shared.usage.nicegui import consume_usage_for_current_user, get_usage_summary_for_current_user

app.include_router(phase2_billing_router)
app.include_router(stripe_webhook_router)
app.include_router(usage_router)
app.add_middleware(NiceGUIAuthMiddleware)

logger = logging.getLogger(__name__)


@app.get("/healthz")
@app.get("/health")
async def healthcheck() -> Dict[str, str]:
    return {"status": "ok", "service": "kotomigaki"}


@app.get("/readyz")
async def readiness() -> JSONResponse:
    from core.site_health.vulnerability_db_bootstrap import vulnerability_database_status

    status = vulnerability_database_status()
    return JSONResponse(status, status_code=200 if status.get("ready") else 503)


async def _ensure_usage_credit_available(service_key: str) -> bool:
    try:
        summary = await get_usage_summary_for_current_user(service_key=service_key)
    except Exception:
        logger.exception("Usage credit check failed for service_key=%s", service_key)
        ui.notify("クレジット確認に失敗しました。時間をおいて再度お試しください。", color="negative")
        return False
    if int(summary.get("remaining_credits") or 0) <= 0:
        ui.notify("クレジットが不足しています。契約管理画面で残高をご確認ください。", color="warning")
        return False
    return True


async def _consume_usage_credit_after_success(*, service_key: str, action_key: str, attempt_id: str) -> bool:
    try:
        summary = await consume_usage_for_current_user(
            service_key=service_key,
            action_key=action_key,
            units=1,
            idempotency_key=f"{service_key}:{action_key}:{attempt_id}",
            metadata={"trigger": "post_success"},
        )
        logger.info(
            "Usage credit debited service_key=%s action_key=%s attempt_id=%s event_id=%s remaining=%s replay=%s",
            service_key,
            action_key,
            attempt_id,
            summary.get("usage_event_id"),
            summary.get("remaining_credits"),
            summary.get("idempotent_replay"),
        )
        return True
    except Exception:
        logger.exception("Usage credit debit failed for service_key=%s action_key=%s", service_key, action_key)
        ui.notify("処理は完了しましたが、クレジット消費の記録に失敗しました。管理者へ連絡してください。", color="negative")
        return False

def _get_resource_dir() -> Path:
    """Directory for bundled read-only resources (onefile temp dir)."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent

def _get_exe_dir() -> Path:
    """Directory next to the executable (persistent writable)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

RESOURCE_DIR = _get_resource_dir()
EXE_DIR = _get_exe_dir()

ASSETS_DIR = RESOURCE_DIR / "assets"

# Hub URL (top page) — sanitize env vars to prevent HTML injection
def _safe_url(val: str) -> str:
    """Remove characters that could break HTML attribute context."""
    return val.replace('"', '').replace("'", '').replace('<', '').replace('>', '').strip()

HUB_URL = _safe_url(os.environ.get("HUB_URL", "https://app.techie.jp"))
KOTOMAKE_URL = _safe_url(os.environ.get("KOTOMAKE_URL", "https://kotomake.ashymushroom-021a53c5.japanwest.azurecontainerapps.io"))
KOTOMIGAKI_URL = _safe_url(os.environ.get("KOTOMIGAKI_URL", "https://kotomigaki.ashymushroom-021a53c5.japanwest.azurecontainerapps.io"))
KOTOMEGANE_URL = _safe_url(os.environ.get("KOTOMEGANE_URL", "https://kotomegane.ashymushroom-021a53c5.japanwest.azurecontainerapps.io"))

# Allow only the tags/attrs we use in ui.html
def _sanitize_href_allow_file(href: str) -> str:
    if href.startswith(("/", "mailto:", "http:", "https:", "#", "tel:", "file:")):
        return href
    return "#"

# Allow only the tags/attrs we use in ui.html
HTML_SANITIZER = Sanitizer({
    "tags": {"nav", "a", "span", "img"},
    "attributes": {
        "a": ("href", "class"),
        "nav": ("class",),
        "span": ("class",),
        "img": ("src", "alt", "class"),
    },
    "empty": {"img"},
    "separate": {"a", "span", "nav", "img"},
    "sanitize_href": _sanitize_href_allow_file,
})

@dataclass

class AppState:

    analyzer: Optional[SEOAIOAnalyzer] = None

    results: Optional[Dict[str, Any]] = None

    competitor_results: Optional[Dict[str, Any]] = None

    competitor_action_advice: Optional[Dict[str, Any]] = None

    competitor_blocked: Optional[str] = None

    competitor_error: Optional[str] = None

    last_run_id: Optional[int] = None

    busy: bool = False

    display_mode: str = "advanced"
    plain_language_mode: bool = True

    url_type_selected: str = "自動判定"

    progress_started_at: Optional[datetime] = None
    progress_stage: Optional[str] = None
    progress_detail: Optional[str] = None
    progress_percent: float = 0.0
    progress_log: List[Dict[str, Any]] = field(default_factory=list)
    result_expansions: List[Any] = field(default_factory=list)
    report_expansions: List[Any] = field(default_factory=list)

state = AppState()

def _build_user_error_message(error_text: str) -> str:
    """Translate internal errors into user-facing Japanese messages."""
    lower_text = (error_text or "").lower()

    if "max tokens" in lower_text or "max_output_tokens" in lower_text or "maximum context" in lower_text:
        return "トークン上限に達しました。入力URLか出力範囲を調整してください。"
    if "api" in lower_text and "key" in lower_text:
        return "APIキーの設定に問題があります。OpenAI APIキーの権限と残高を確認してください。"
    if "timeout" in lower_text or "timed out" in lower_text or "connection" in lower_text:
        return "URLへの接続がタイムアウトしました。URLを確認して再試行してください。"
    if "404" in lower_text:
        return "URLが見つかりません（404）。URLを確認してください。"
    if "403" in lower_text or "forbidden" in lower_text:
        return "このサイトはクロールをブロックしています（403 Forbidden）。"
    if "429" in lower_text or "robots" in lower_text:
        return "取得制限のため分析できませんでした。robots.txtやアクセス制限を確認してください。"
    return "分析中にエラーが発生しました。URL形式、ネットワーク、API設定を確認して再実行してください。"


_HOST_ONLY_PATTERN = re.compile(
    r"^(localhost|(?:\d{1,3}\.){3}\d{1,3}|[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,})(?:[/:?#].*)?$"
)


def _normalize_input_url(raw_url: str) -> str:
    value = (raw_url or "").strip()
    if not value:
        return ""
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", value):
        return value
    if _HOST_ONLY_PATTERN.match(value):
        return f"https://{value}"
    return value


def _is_valid_input_hostname(hostname: str) -> bool:
    if not hostname:
        return False
    if hostname == "localhost":
        return True
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return "." in hostname and all(part for part in hostname.split("."))


def _validate_analysis_input_url(raw_url: str, *, label: str, required: bool) -> tuple[str, Optional[str]]:
    value = (raw_url or "").strip()
    if not value:
        if required:
            return "", f"{label}を入力してください。"
        return "", None
    if re.search(r"\s", value):
        return value, f"{label}に空白が含まれています。"

    normalized = _normalize_input_url(value)
    parsed = urlparse(normalized)
    scheme = (parsed.scheme or "").lower()
    if scheme not in {"http", "https"} or not parsed.netloc:
        return normalized, f"{label}は http:// または https:// で始まる形式で入力してください。"
    if not _is_valid_input_hostname(parsed.hostname or ""):
        return normalized, f"{label}のドメイン形式を確認してください。"
    return normalized, None


def _build_auto_open_note(auto_open_enabled: bool) -> str:
    if auto_open_enabled:
        return "分析結果は自動保存します。完了後は保存済みワークスペースを自動で開きます。"
    return "分析結果は自動保存します。完了後はこの画面にとどまり、必要なときだけ保存結果を開けます。"


def _build_completion_progress_text(auto_open_enabled: bool) -> str:
    if auto_open_enabled:
        return "進捗: 完了 - 保存済みワークスペースを開きます (100%)"
    return "進捗: 完了 - この画面にとどまります (100%)"


def _build_saved_run_status_text(auto_open_enabled: bool) -> str:
    if auto_open_enabled:
        return "分析結果を保存しました。自動で開かない場合は右のボタンから保存結果を開いてください。"
    return "分析結果を保存しました。この画面にとどまっています。必要なときだけ右のボタンから保存結果を開いてください。"


def _push_progress_update(stage: str, percent: float, detail: Optional[str] = None) -> None:
    """Update shared UI progress state without breaking callers on formatting differences."""
    safe_percent = max(0.0, min(percent, 1.0))
    state.progress_stage = stage
    state.progress_detail = detail
    state.progress_percent = safe_percent
    state.progress_log.append(
        {
            "stage": stage,
            "percent": round(safe_percent, 3),
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
        }
    )


def _reset_progress_state() -> None:
    state.progress_started_at = None
    state.progress_stage = None
    state.progress_detail = None
    state.progress_percent = 0.0
    state.progress_log = []

def calc_citation_index(citation: Optional[Dict[str, Any]]) -> Optional[float]:

    if not citation:

        return None

    axes = citation.get("axes", [])

    scores = []

    for axis in axes:

        try:

            scores.append(float(axis.get("quality_score", 0)))

        except Exception:

            continue

    if not scores:

        return None

    return sum(scores) / len(scores)

def ensure_analyzer() -> SEOAIOAnalyzer:

    if state.analyzer is None:

        state.analyzer = SEOAIOAnalyzer(analysis_mode="standard")

    return state.analyzer

AIO_SCORE_LABELS_STANDARD = {
    "pid_density": "命題密度 (PID)",
    "structure": "構造",
    "entity_salience": "エンティティ重要度",
    "technical": "技術的AIO適合性",
    "citation": "引用準備度",
    "freshness": "情報鮮度",
    "aeo": "AEOパターン",
    "entity_linking": "知識グラフ連携",
    "experience": "経験 (Experience)",
    "expertise": "専門性 (Expertise)",
    "authoritativeness": "権威性 (Authoritativeness)",
    "trustworthiness": "信頼性 (Trustworthiness)",
    # P06: E-E-A-T + GEO指標
    "eeat": "E-E-A-T（著者・組織の信頼性）",
    "geo_tldr": "TL;DR 冒頭要約（GEO）",
    "geo_stats": "統計・数値密度（GEO）",
}

AIO_SCORE_HELP_STANDARD = {
    "pid_density": "主張や結論が明確に示されている度合いです。",
    "structure": "見出し構造や論理展開の整理度合いです。",
    "entity_salience": "固有名詞や専門用語など重要エンティティの明確さです。",
    "technical": "構造化データや技術要素の充実度です。",
    "citation": "AIがそのまま要点を引用しやすい文・段落構造かを見ます。",
    "freshness": "更新日や最新性の手掛かりがあるかを見ます。",
    "aeo": "FAQや定義文など、AIが答えにしやすい型を見ます。",
    "entity_linking": "固有名詞や専門用語の関係がはっきりしているかを見ます。",
    "experience": "一次体験・実務経験の記述があるかです。",
    "expertise": "専門性の高さが示されているかです。",
    "authoritativeness": "権威性・参照可能性が示されているかです。",
    "trustworthiness": "信頼性や根拠が担保されているかです。",
    # P06: E-E-A-T + GEO指標
    "eeat": "著者名・資格・組織情報・一次情報シグナルの有無。AI検索での引用判断に直結（重み8%）。",
    "geo_tldr": "ページ先頭に「この記事のポイント」等の要約があるか。AI引用率+30〜40%向上（重み5%）。",
    "geo_stats": "数値・割合・調査データ・外部引用の密度。高いほどAI可視性が上がる（重み5%）。",
}

AIO_SCORE_LABELS_PLAIN = {
    "pid_density": "要点の伝わりやすさ",
    "structure": "読みやすい構成",
    "entity_salience": "固有名詞・専門語の明確さ",
    "technical": "技術面の整備度",
    "citation": "引用しやすい書き方",
    "freshness": "情報の新しさ",
    "aeo": "Q&A / 定義のわかりやすさ",
    "entity_linking": "用語のつながりの明確さ",
    "experience": "体験・実績の記載",
    "expertise": "専門知識の伝わりやすさ",
    "authoritativeness": "信頼できる情報源か",
    "trustworthiness": "根拠と透明性",
    "eeat": "著者・運営者の信頼情報",
    "geo_tldr": "冒頭の要点まとめ",
    "geo_stats": "数値・データの具体性",
}

AIO_SCORE_HELP_PLAIN = {
    "pid_density": "結論や主張がはっきり書かれているほど高くなります。",
    "structure": "見出しや段落の流れが整理されているほど高くなります。",
    "entity_salience": "会社名・製品名・専門語が具体的に書かれているほど高くなります。",
    "technical": "構造化データや基本設定が整っているほど高くなります。",
    "citation": "要点だけを抜き出しても意味が通るほど高くなります。",
    "freshness": "更新日や最新版の記載があるほど高くなります。",
    "aeo": "Q&Aや定義文があるほど、AIが答えに使いやすくなります。",
    "entity_linking": "用語の関係がわかるほど、AIが文脈を理解しやすくなります。",
    "experience": "実体験や実務に基づく記述があるほど高くなります。",
    "expertise": "専門知識がわかりやすく示されているほど高くなります。",
    "authoritativeness": "信頼できる情報源や実績が示されているほど高くなります。",
    "trustworthiness": "根拠・出典・運営情報が明記されているほど高くなります。",
    "eeat": "著者名・資格・組織情報・一次情報の記載状況です。",
    "geo_tldr": "冒頭に要点がまとまっているほど、引用されやすくなります。",
    "geo_stats": "数値や調査データが具体的なほど、説明の信頼性が上がります。",
}


def get_aio_ui_copy(plain_language_mode: bool) -> tuple[Dict[str, str], Dict[str, str]]:
    if plain_language_mode:
        return dict(AIO_SCORE_LABELS_PLAIN), dict(AIO_SCORE_HELP_PLAIN)
    return dict(AIO_SCORE_LABELS_STANDARD), dict(AIO_SCORE_HELP_STANDARD)


def add_info_tooltip(
    text: str,
    *,
    icon_classes: str = "text-sm text-[#9B7A60] opacity-70 cursor-help",
) -> None:
    ui.icon("info_outline").classes(icon_classes).tooltip(text)


AIO_SCORE_LABELS = dict(AIO_SCORE_LABELS_STANDARD)
AIO_SCORE_HELP = dict(AIO_SCORE_HELP_STANDARD)

PLATFORM_OPTIONS = [

    "WordPress",

    "Wix",

    "Shopify",

    "Amazonマーケットプレイス",

    "楽天市場",

    "Yahoo!ショッピング",

    "BASE",

    "STUDIO",

    "ペライチ",

    "Jimdo",

    "Google Sites",

    "STORES",

    "カラーミーショップ",

    "MakeShop",

    "ショップサーブ",

    "フューチャーショップ",

    "カスタム/その他",

    "自動判定",

]

PLATFORM_OPTION_LABELS = {
    option: (
        "おまかせ（自動で判定）"
        if option == "自動判定"
        else "その他 / 独自設定"
        if option == "カスタム/その他"
        else option
    )
    for option in PLATFORM_OPTIONS
}

URL_TYPE_OPTIONS = [

    "自動判定",

    "企業",

    "EC",

    "企業（EC機能あり）",

    "その他",

]

URL_TYPE_OPTION_LABELS = {
    "自動判定": "おまかせ（自動で見立て）",
    "企業": "企業サイト",
    "EC": "ネットショップ",
    "企業（EC機能あり）": "企業サイト（購入機能あり）",
    "その他": "その他",
}

INDUSTRY_OPTION_LABELS = {
    "自動判定": "おまかせ（自動で見立て）",
    "化粧品・美容": "化粧品・美容",
    "健康食品・サプリメント": "健康食品・サプリメント",
    "医療・クリニック": "医療・クリニック",
    "不動産・住宅": "不動産・住宅",
    "金融・保険": "金融・保険",
    "人材・求人": "人材・求人",
    "教育・スクール": "教育・スクール",
    "法律・士業": "法律・士業",
    "IT・SaaS": "IT・SaaS",
    "飲食・フード": "飲食・フード",
    "小売・EC": "小売・EC",
    "製造業": "製造業",
    "建設・建築": "建設・建築",
    "その他": "その他",
}

def trim_text(value: str, limit: int = 120) -> str:
    """
    Trim text to specified limit while respecting word/sentence boundaries.
    """
    if not value:
        return ""

    if len(value) <= limit:
        return value

    # Find a good breaking point (period, comma, or space) near the limit
    truncated = value[:limit]

    # Look for Japanese sentence endings (。！？) or punctuation
    for delimiter in ['。', '！', '？', '、']:
        last_delimiter = truncated.rfind(delimiter)
        if last_delimiter > limit * 0.7:  # At least 70% of the limit
            return value[:last_delimiter + 1]

    # Look for spaces (for English/mixed text)
    last_space = truncated.rfind(' ')
    if last_space > limit * 0.7:
        return value[:last_space] + "..."

    # If no good breaking point found, just cut at limit
    return value[:max(limit - 3, 0)] + "..."

def format_reason_text_ui(value: str) -> str:
    if not value:
        return ""
    normalized = re.sub(r"(?<!\n)■", "\n■", value)
    normalized = re.sub(r"(?<!\n)【", "\n【", normalized)
    normalized = re.sub(r"(?<!\n)[・･•]", lambda m: "\n" + m.group(0), normalized)
    replacements = [
        ("■ 自動判定業界での重要ポイント:", "■ 今回のサイトに近い業界で重視したポイント:"),
        ("ユーザー入力（自動判定で確認済み）", "入力内容を優先（自動推定でも一致）"),
        ("ユーザー入力（自動判定:", "入力内容を優先（自動推定:"),
        ("自動判定:", "自動推定:"),
        ("■ カスタム/その他での改善手順:", "■ その他 / 独自設定サイトでの改善手順:"),
        ("【カスタム/その他】", "【その他 / 独自設定】"),
        ("カスタム/その他で", "その他 / 独自設定サイトで"),
        ("カスタム/その他", "その他 / 独自設定"),
        ("AI検索の引用源(Source)", "AI検索で参照されやすい引用元"),
        ("E-E-A-T不足", "著者・運営者の信頼情報が不足"),
        ("TL;DR", "冒頭要点まとめ"),
        ("E-E-A-T", "著者・運営者の信頼情報"),
    ]
    for old, new in replacements:
        normalized = normalized.replace(old, new)
    return "\n".join(line.strip() for line in normalized.splitlines() if line.strip())


_initial_aio_score_labels, _initial_aio_score_help = get_aio_ui_copy(state.plain_language_mode)

bind_panel_dependencies(
    state=state,
    trim_text=trim_text,
    format_reason_text_ui=format_reason_text_ui,
    calc_citation_index=calc_citation_index,
    aio_score_labels=_initial_aio_score_labels,
    aio_score_help=_initial_aio_score_help,
)

ui.add_head_html(

    """

    <link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    <style>

      :root {

        --bg: #F7F1EA;

        --bg-deep: #F1E2D4;

        --surface: #FFFDF9;

        --surface-muted: #FBF7F2;

        --text: #2F241D;

        --text-muted: #6B5A4D;

        --muted: var(--text-muted);

        --accent: #D96B1F;

        --accent-2: #B95416;

        --accent-soft: rgba(217, 107, 31, 0.12);

        --support-soft: rgba(217, 107, 31, 0.10);

        --border: rgba(191, 174, 159, 0.72);

        --border-strong: rgba(191, 174, 159, 0.90);

        --shadow: 0 10px 28px rgba(42, 31, 26, 0.08);

        --shadow-hover: 0 14px 36px rgba(42, 31, 26, 0.12);

        --nav-bg: #2F241D;

        --nav-text: #E7DDD4;

        --nav-text-hover: #FFFFFF;

        --nav-text-active: #F5BA71;

        --nav-height: 52px;

        --logo-height: 64px;

        --q-primary: #D96B1F;
        --q-secondary: #9B7A60;
        --q-accent: #B95416;
        --q-dark: #2F241D;
        --q-positive: #2F7A52;
        --q-negative: #B42318;
        --q-info: #9B7A60;
        --q-warning: #C77700;

      }

      body {

        font-family: 'Sora', 'Noto Sans JP', 'Hiragino Sans', 'Meiryo', sans-serif;

        font-size: 17px;

        background: linear-gradient(160deg, var(--bg) 0%, var(--bg-deep) 50%, var(--bg) 100%);

        color: var(--text);

        min-height: 100vh;

      }

      html {

        font-size: 17px;

      }

      .app-shell {

        max-width: 1200px;

        margin: calc(var(--nav-height) + 28px) auto 80px;

        padding: 0 20px;

        width: 100%;

      }

      .hero {

        margin-bottom: 24px;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 6px;

      }

      .hero-logo {

        width: min(100%, 220px);
        max-width: 220px;
        height: auto;

        object-fit: contain;
        display: block;

      }

      .hero-brand-row {

        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 18px;

      }

      .hero-brand-copy {

        display: flex;
        flex-direction: column;
        gap: 4px;

      }

      .hero-service-name {

        font-size: 22px;
        font-weight: 700;
        color: var(--accent);
        line-height: 1.1;

      }

      .hero-service-note {

        color: var(--text-muted);
        font-size: 13px;
        font-weight: 600;

      }

      .hero-sub {

        color: var(--text-muted);

        font-size: 15px;
        line-height: 1.55;
        max-width: 720px;

        margin-top: 2px;

      }

      .hero-shell {

        display: grid;
        grid-template-columns: minmax(0, 1fr);
        gap: 16px;
        align-items: start;
        justify-items: start;
        margin-bottom: 18px;

      }

      .hero-copy {

        background:
          radial-gradient(circle at top right, var(--support-soft), transparent 42%),
          linear-gradient(140deg, rgba(255, 247, 239, 0.96), rgba(255, 252, 246, 0.94));
        border: 1px solid rgba(230, 68, 36, 0.12);
        border-radius: 22px;
        padding: 16px 18px;
        box-shadow: var(--shadow);
        width: 100%;

      }

      .dashboard-analyze-card {
        border-top: 4px solid var(--accent-2);
        background:
          radial-gradient(circle at top right, rgba(217, 107, 31, 0.08), transparent 36%),
          linear-gradient(180deg, rgba(255, 252, 247, 0.98), rgba(255, 250, 245, 1));
      }

      .dashboard-analyze-grid {
        display: grid;
        grid-template-columns: minmax(0, 1.45fr) minmax(220px, 0.55fr);
        gap: 18px;
        align-items: start;
      }

      .dashboard-analyze-side {
        min-width: 0;
      }

      .dashboard-side-panel {
        border-radius: 16px;
        border: 1px solid rgba(191, 174, 159, 0.72);
        background: rgba(255, 255, 255, 0.76);
        padding: 16px;
      }

      .dashboard-side-kicker {
        font-size: 11px !important;
        letter-spacing: 0.08em;
        color: var(--accent);
        font-weight: 700;
      }

      .dashboard-side-title {
        font-size: 16px !important;
        font-weight: 700;
        color: var(--text);
      }

      .dashboard-side-point {
        font-size: 13px !important;
        line-height: 1.65;
        color: var(--text-muted);
      }

      .dashboard-analyze-form {
        display: flex;
        flex-direction: column;
        gap: 14px;
      }

      .dashboard-analyze-note {
        font-size: 12px !important;
        line-height: 1.6;
        color: var(--text-muted);
      }

      .dashboard-status-bar {
        min-height: 28px;
      }

      .dashboard-toolbar-card {
        background: rgba(255, 252, 246, 0.88);
      }

      .dashboard-brand-strip {
        padding: 14px 16px;
      }

      .dashboard-brand-strip .hero-logo {
        width: min(100%, 148px);
        max-width: 148px;
      }

      .dashboard-utility-link {
        color: #7A3A16;
        text-decoration: none;
        font-size: 13px;
        font-weight: 700;
        line-height: 1.5;
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }

      .dashboard-utility-link:hover {
        color: var(--accent-2);
        text-decoration: underline;
      }

      .hero-kicker {

        letter-spacing: 0.08em;
        font-size: 12px;
        color: var(--accent);
        font-weight: 700;

      }

      .q-tooltip {
        font-size: 14px !important;
        line-height: 1.65 !important;
        max-width: 340px;
        padding: 10px 12px !important;
        background: rgba(36, 24, 19, 0.94) !important;
        color: #FFF8F1 !important;
        border-radius: 12px !important;
      }

      .hero-chip {

        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 5px 10px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid rgba(230, 68, 36, 0.14);
        color: var(--text);
        font-size: 12px;
        font-weight: 600;

      }

      .input-grid {

        display: grid;
        grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.85fr);
        gap: 20px;
        align-items: start;
        margin-bottom: 22px;

      }

      .workspace-grid {

        display: grid;
        grid-template-columns: minmax(320px, 0.75fr) minmax(0, 1.25fr);
        gap: 24px;
        align-items: start;

      }

      .analysis-stack {

        display: flex;
        flex-direction: column;
        gap: 18px;

      }

      .results-container,
      .report-container {

        scroll-margin-top: calc(var(--nav-height) + 88px);

      }

      .compact-expansion .q-expansion-item__container {

        border-radius: 14px;
        border: 1px solid rgba(36, 24, 19, 0.08);
        background: rgba(255, 252, 246, 0.82);

      }

      .compact-expansion .q-expansion-item__content {

        background: transparent;

      }

      .summary-rail {

        position: sticky;
        top: calc(var(--nav-height) + 78px);
        align-self: start;

      }

      .workbench-pane {

        min-width: 0;

      }

      .diff-wrap {

        line-height: 1.6;

      }

      .diff-line {

        padding: 4px 6px;

        border-radius: 8px;

        background: rgba(217, 107, 31, 0.08);

      }

      .diff-label {

        display: inline-block;

        min-width: 64px;

        font-weight: 700;

        color: #7A3A16;

      }

      .diff-index {

        font-weight: 700;

        margin-right: 6px;

      }

      .diff-add {

        font-weight: 700;

        background: rgba(217, 107, 31, 0.18);

        border-radius: 6px;

        padding: 0 3px;

      }

      .diff-del {

        text-decoration: line-through;

        color: rgba(13, 17, 23, 0.5);

        background: rgba(239, 68, 68, 0.12);

        border-radius: 6px;

        padding: 0 3px;

      }

      .card {

        background: var(--surface);

        border-radius: 18px;

        border: 2px solid var(--border-strong);

        box-shadow: var(--shadow);
        transition: transform 0.2s ease, box-shadow 0.2s ease;

      }

      .card:hover {

        transform: translateY(-2px);

        box-shadow: var(--shadow-hover);

      }

      .card-title {

        font-size: 18px !important;

        font-weight: 600;

        color: var(--text);

      }

      .card-sub {

        font-size: 15px !important;
        line-height: 1.7;

        color: var(--text);

      }

      .card-hint {

        font-size: 13px !important;
        line-height: 1.6;
        color: var(--text-muted);

      }

      .fixed-chip {

        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 11px !important;
        font-weight: 700;
        letter-spacing: 0.04em;
        color: #8a5a00;
        background: rgba(202, 138, 4, 0.14);
        border: 1px solid rgba(202, 138, 4, 0.18);

      }

      .fixed-note {

        font-size: 13px !important;
        line-height: 1.6;
        color: var(--text-muted);

      }

      .generated-block {

        border-color: rgba(217, 107, 31, 0.16);
        background: linear-gradient(180deg, rgba(255, 255, 255, 1), rgba(255, 248, 241, 0.98));

      }

      .implementation-note-card {

        border-color: rgba(202, 138, 4, 0.22);
        background: linear-gradient(180deg, rgba(255, 251, 235, 0.98), rgba(255, 247, 237, 0.99));

      }

      .diagnostic-note-card {

        border-color: rgba(122, 98, 83, 0.16);
        background: linear-gradient(180deg, rgba(255, 255, 255, 1), rgba(250, 244, 237, 0.96));

      }

      .reference-note-card {

        border-color: rgba(191, 174, 159, 0.56);
        background: linear-gradient(180deg, rgba(255, 255, 255, 1), rgba(251, 247, 242, 0.96));

      }

      .generated-chip {

        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 11px !important;
        font-weight: 700;
        letter-spacing: 0.04em;
        color: #7A3A16;
        background: rgba(217, 107, 31, 0.12);
        border: 1px solid rgba(217, 107, 31, 0.18);

      }

      .generated-title {

        font-size: 16px !important;
        font-weight: 700;
        line-height: 1.5;
        color: var(--text);
        margin-top: 8px;

      }

      .generated-body {

        font-size: 14px !important;
        line-height: 1.7;
        color: var(--text);
        margin-top: 6px;

      }

      .generated-metric {

        font-size: 11px !important;
        line-height: 1.5;
        color: #0b6e61;

      }

      .evaluation-summary-card {
        border-color: rgba(217, 107, 31, 0.18);
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.99), rgba(255, 248, 241, 0.98));
      }

      .evaluation-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
      }

      .evaluation-card {
        min-height: 164px;
      }

      .evaluation-label {
        font-size: 12px !important;
        font-weight: 700;
        color: var(--text-muted);
        letter-spacing: 0.04em;
      }

      .evaluation-score {
        font-size: 42px !important;
        line-height: 1;
        font-weight: 700;
        color: var(--text);
      }

      .evaluation-score-scale {
        font-size: 16px !important;
        color: var(--text-muted);
        padding-bottom: 3px;
      }

      .evaluation-reason-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }

      .evaluation-reason-card {
        min-height: 138px;
      }

      .workspace-shell {

        display: grid;
        grid-template-columns: 220px minmax(0, 1fr);
        gap: 24px;
        align-items: start;

      }

      .workspace-nav {

        position: sticky;
        top: calc(var(--nav-height) + 72px);
        padding: 16px 14px;
        border: 1px solid rgba(36, 24, 19, 0.12);
        border-radius: 18px;
        background: linear-gradient(180deg, rgba(255, 252, 246, 0.98), rgba(247, 240, 229, 0.94));
        box-shadow: var(--shadow);

      }

      .workspace-nav-tabs .q-tab {

        justify-content: flex-start;
        min-height: 48px;
        padding: 10px 12px;
        border-radius: 14px;
        color: var(--text-muted);
        margin-bottom: 6px;

      }

      .workspace-nav-tabs .q-tab--active {

        background: linear-gradient(135deg, rgba(230, 68, 36, 0.14), rgba(185, 106, 54, 0.08));
        border: 1px solid rgba(230, 68, 36, 0.14);
        color: var(--text);
        font-weight: 600;

      }

      .workspace-panel {

        border-radius: 20px;

      }

      .action-preview-card {

        min-height: 150px;

      }

      .action-preview-title {

        font-size: 16px !important;
        font-weight: 700;
        line-height: 1.45;
        color: var(--text);

      }

      .action-preview-body {

        font-size: 14px !important;
        line-height: 1.65;
        color: var(--text);

      }

      .action-preview-meta {
 
        font-size: 12px !important;
        line-height: 1.5;
        color: var(--text-muted);
 
      }

      .dashboard-history-desktop {
        display: block;
      }

      .dashboard-history-mobile {
        display: none;
      }

      .dashboard-top-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 16px;
        align-items: stretch;
      }

      .dashboard-overview-card {
        min-height: 232px;
      }

      .dashboard-alert-chip {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 28px;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(230, 68, 36, 0.12);
        color: var(--accent);
        font-size: 11px !important;
        font-weight: 700;
        letter-spacing: 0.05em;
      }

      .dashboard-overview-score {
        font-size: 52px !important;
        line-height: 1;
        font-weight: 700;
        color: var(--text);
      }

      .dashboard-overview-score-scale {
        font-size: 24px !important;
        line-height: 1.2;
        color: var(--text-muted);
        padding-bottom: 6px;
      }

      .dashboard-overview-diff {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 30px;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(217, 107, 31, 0.10);
        color: #7A3A16;
        font-size: 12px !important;
        font-weight: 700;
        margin-bottom: 6px;
      }

      .dashboard-mini-metric {
        flex: 1;
        min-width: 120px;
        padding: 12px 14px;
        border-radius: 14px;
        background: rgba(255, 251, 246, 0.92);
        border: 1px solid rgba(191, 174, 159, 0.56);
      }

      .dashboard-mini-label {
        font-size: 12px !important;
        line-height: 1.5;
        color: var(--text-muted);
      }

      .dashboard-action-card {
        border-width: 1px;
      }

      .dashboard-action-critical {
        background: linear-gradient(180deg, rgba(255, 245, 245, 0.98), rgba(255, 251, 250, 0.98));
        border-color: rgba(225, 29, 72, 0.16);
      }

      .dashboard-action-warn {
        background: linear-gradient(180deg, rgba(255, 250, 240, 0.98), rgba(255, 252, 246, 0.98));
        border-color: rgba(217, 119, 6, 0.16);
      }

      .dashboard-action-soft {
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(251, 247, 242, 0.98));
        border-color: rgba(191, 174, 159, 0.56);
      }

      .dashboard-action-chip {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 11px !important;
        font-weight: 700;
        letter-spacing: 0.04em;
        background: rgba(255, 255, 255, 0.76);
        color: var(--text);
        border: 1px solid rgba(36, 24, 19, 0.08);
      }

      .dashboard-mini-value {
        font-size: 24px !important;
        line-height: 1.2;
        font-weight: 700;
        color: var(--text);
      }

      .dashboard-summary-row {
        padding: 12px 14px;
        border-radius: 14px;
        background: rgba(255, 251, 246, 0.92);
        border: 1px solid rgba(191, 174, 159, 0.56);
      }

      .dashboard-summary-value {
        font-size: 28px !important;
        line-height: 1.2;
        font-weight: 700;
        color: var(--text);
      }

      .history-kpi-chip {
        min-width: 120px;
        padding: 10px 12px;
        border-radius: 14px;
        background: rgba(248, 250, 252, 0.92);
        border: 1px solid rgba(148, 163, 184, 0.18);
      }

      .history-kpi-value {
        font-size: 20px !important;
        line-height: 1.2;
        font-weight: 700;
        color: var(--text);
      }

      .dashboard-history-list {
        display: flex;
        flex-direction: column;
        gap: 10px;
      }

      .dashboard-history-card {
        padding: 14px 14px 12px;
        cursor: pointer;
      }

      .dashboard-history-head {
        justify-content: space-between;
        gap: 12px;
      }

      .dashboard-history-url {
        font-size: 15px !important;
        font-weight: 700;
        line-height: 1.4;
        color: var(--text);
        word-break: break-all;
      }

      .dashboard-history-date {
        font-size: 12px !important;
        line-height: 1.4;
        color: var(--text-muted);
      }

      .dashboard-priority-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 44px;
        padding: 5px 10px;
        border-radius: 999px;
        font-size: 11px !important;
        font-weight: 700;
        letter-spacing: 0.04em;
      }

      .dashboard-priority-high {
        background: rgba(230, 68, 36, 0.16);
        color: #9f2d18;
      }

      .dashboard-priority-mid {
        background: rgba(202, 138, 4, 0.16);
        color: #8a5a00;
      }

      .dashboard-priority-low {
        background: rgba(245, 186, 113, 0.18);
        color: #7A3A16;
      }

      .dashboard-history-issues {
        font-size: 11px !important;
        line-height: 1.3;
        color: var(--text-muted);
        margin-top: 4px;
      }

      .dashboard-score-stack {
        gap: 8px;
        margin-top: 8px;
      }

      .dashboard-score-row {
        gap: 8px;
      }

      .dashboard-score-label {
        width: 28px;
        font-size: 10px !important;
        font-weight: 700;
        letter-spacing: 0.06em;
        color: var(--text-muted);
      }

      .dashboard-score-track {
        position: relative;
        flex: 1;
        height: 9px;
        border-radius: 999px;
        overflow: hidden;
        background: rgba(36, 24, 19, 0.08);
      }

      .dashboard-score-fill {
        height: 100%;
        border-radius: 999px;
      }

      .dashboard-score-ai {
        background: linear-gradient(90deg, #F5BA71, #D96B1F);
      }

      .dashboard-score-seo {
        background: linear-gradient(90deg, #A05A2C, #7A3A16);
      }

      .dashboard-score-value {
        width: 30px;
        text-align: right;
        font-size: 12px !important;
        font-weight: 700;
        color: var(--text);
      }

      .dashboard-history-action {
        font-size: 13px !important;
        line-height: 1.45;
        color: var(--text);
        margin-top: 10px;
      }

      .dashboard-history-chevron {
        font-size: 16px !important;
        color: var(--text-muted);
      }

      .dashboard-history-mobile-hint {
        font-size: 12px !important;
        line-height: 1.4;
        color: #5A463B;
        font-weight: 600;
        text-align: center;
      }

      .compact-note-list {
 
        display: flex;
        flex-direction: column;
        gap: 12px;

      }

      .compact-note-row {

        border: 1px solid var(--border);
        border-radius: 16px;
        background: rgba(255, 252, 246, 0.82);
        padding: 14px 16px;

      }

      .badge {

        background: rgba(217,107,31,0.12);

        color: #7A3A16;

        padding: 4px 10px;

        border-radius: 999px;

        font-size: 14px !important;

        font-weight: 600;

      }

      .input-label {

        font-size: 15px !important;

        color: var(--text);

        margin-bottom: 4px;

      }

      .primary-btn {

        background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;

        color: #ffffff !important;

        border-radius: 10px;

        font-weight: 600;
        min-height: 44px;
        padding: 0 18px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 8px 18px rgba(42, 31, 26, 0.12);
        transition: transform 0.15s ease, box-shadow 0.15s ease;

      }

      .q-btn.primary-btn {
        background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
        background-color: var(--accent) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 8px 18px rgba(42, 31, 26, 0.12) !important;
      }

      .q-btn.primary-btn.bg-primary,
      .q-btn.primary-btn[class*="bg-primary"] {
        background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
        background-color: var(--accent) !important;
        color: #ffffff !important;
      }

      .q-btn.bg-primary:not(.q-btn--disabled),
      .q-btn[class*="bg-primary"]:not(.q-btn--disabled) {
        background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
        background-color: var(--accent) !important;
        color: #ffffff !important;
      }

      .q-btn.bg-primary .q-btn__content,
      .q-btn[class*="bg-primary"] .q-btn__content {
        color: #ffffff !important;
      }

      .q-btn.primary-btn .q-btn__content {
        color: #ffffff !important;
        font-weight: 700 !important;
      }

      .q-btn.primary-btn::before,
      .q-btn.primary-btn .q-focus-helper {
        background: transparent !important;
        opacity: 0 !important;
      }

      .primary-btn:hover {

        transform: translateY(-1px);
        box-shadow: 0 12px 24px rgba(42, 31, 26, 0.16);

      }

      .secondary-btn {
        background: rgba(255, 251, 246, 0.96) !important;
        color: #7A3A16 !important;
        border: 1px solid rgba(122, 98, 83, 0.18) !important;
        border-radius: 10px;
        font-weight: 600;
        min-height: 44px;
        padding: 0 18px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        box-shadow: none;
      }

      .q-btn.secondary-btn {
        background: rgba(255, 251, 246, 0.96) !important;
        background-color: rgba(255, 251, 246, 0.96) !important;
        color: #7A3A16 !important;
        border: 1px solid rgba(122, 98, 83, 0.18) !important;
        box-shadow: none !important;
      }

      .q-btn.secondary-btn.bg-primary,
      .q-btn.secondary-btn[class*="bg-primary"],
      .q-btn.bg-primary.secondary-btn,
      .q-btn[class*="bg-primary"].secondary-btn {
        background: rgba(255, 251, 246, 0.96) !important;
        background-color: rgba(255, 251, 246, 0.96) !important;
        color: #7A3A16 !important;
        border: 1px solid rgba(122, 98, 83, 0.18) !important;
      }

      .q-btn.secondary-btn.q-btn--outline {
        background: rgba(255, 251, 246, 0.96) !important;
      }

      .q-btn.secondary-btn .q-btn__content {
        color: #7A3A16 !important;
        font-weight: 700 !important;
      }

      .q-btn.secondary-btn::before,
      .q-btn.secondary-btn .q-focus-helper {
        background: transparent !important;
        opacity: 0 !important;
      }

      .secondary-btn:hover {
        background: rgba(217, 107, 31, 0.08) !important;
        box-shadow: none;
      }

      a:focus-visible,
      button:focus-visible,
      input:focus-visible,
      textarea:focus-visible,
      select:focus-visible,
      .q-btn:focus-visible,
      .q-tab:focus-visible,
      .q-expansion-item__header:focus-visible,
      .q-field__native:focus-visible {
        outline: 3px solid rgba(185, 106, 54, 0.92);
        outline-offset: 3px;
        border-radius: 12px;
      }

      .q-field--focused .q-field__control,
      .q-select.q-field--focused .q-field__control,
      .q-input.q-field--focused .q-field__control {
        box-shadow: 0 0 0 3px rgba(185, 106, 54, 0.18);
        border-color: rgba(185, 106, 54, 0.5) !important;
      }

      .section-grid {

        gap: 18px;

      }

      .metric {

        background: var(--surface-muted);

        border-radius: 16px;

        padding: 14px 16px;

        min-width: 140px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;

      }

      .metric:hover {

        transform: translateY(-2px);

        box-shadow: 0 12px 28px rgba(11, 20, 32, 0.12);

      }

      .metric-value {

        font-size: 28px !important;

        font-weight: 700;

      }

      .metric-label {

        font-size: 14px !important;

        color: var(--text);

      }

      .summary-visual-grid {
        gap: 18px;
        align-items: stretch;
      }

      .summary-radar-card {
        flex: 1 1 420px;
        min-width: 320px;
      }

      .summary-radar-chart {
        min-height: 280px;
      }

      .summary-visual-side {
        flex: 1 1 260px;
        min-width: 250px;
      }

      .summary-axis-score {
        min-width: 28px;
        text-align: right;
        font-size: 12px !important;
        font-weight: 700;
        color: var(--text);
      }

      .summary-alert-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 11px !important;
        font-weight: 700;
        white-space: nowrap;
      }

      .summary-pill-warn {
        background: rgba(217, 107, 31, 0.14);
        color: #9A4D1A;
      }

      .summary-pill-info {
        background: rgba(139, 116, 79, 0.12);
        color: #6B5A45;
      }

      .summary-pill-pass {
        background: rgba(22, 163, 74, 0.12);
        color: #1F7A3D;
      }

      /* Premium Animations */
      @keyframes animateSlideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .animate-slide-up {
        animation: animateSlideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
      }
      .animate-fade-in {
        animation: fadeIn 0.8s ease-out forwards;
      }
      @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      
      /* Animation Delays for Staggering */
      .delay-100 { animation-delay: 100ms; }
      .delay-200 { animation-delay: 200ms; }
      .delay-300 { animation-delay: 300ms; }
      .delay-400 { animation-delay: 400ms; }
      .delay-500 { animation-delay: 500ms; }

      .tabs .q-tabs__content {

        background: rgba(244, 240, 233, 0.92);

        border-radius: 16px;

        padding: 6px;

      }

      .tabs .q-tab {

        min-height: 42px;

        font-weight: 600;

        font-size: 14px !important;
        color: var(--text-muted);
        border-radius: 12px;
        transition: background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;

      }

      .tabs .q-tab--active {

        background: rgba(255, 255, 255, 0.96);

        color: var(--accent-2);

        border-radius: 12px;
        box-shadow: 0 10px 18px rgba(102, 61, 35, 0.08);

      }

      .tabs .q-tab__indicator {

        height: 3px;

        background: var(--accent-2);

        border-radius: 2px;

      }

      .detail-tabs-card {
        overflow: hidden;
      }

      .workspace-tabs .q-tabs__content {
        background: rgba(241, 245, 249, 0.84);
        border: 1px solid rgba(148, 163, 184, 0.16);
      }

      .workspace-tabs .q-tab {
        min-height: 44px;
        font-size: 14px !important;
      }

      .workspace-tabs .q-tab--active {
        color: var(--accent);
        background: rgba(255, 255, 255, 0.98);
      }

      .saved-run-tabs .q-tabs__content {
        background: rgba(244, 237, 228, 0.96);
        border: 1px solid rgba(122, 98, 83, 0.16);
        border-radius: 18px;
        padding: 8px;
        gap: 8px;
      }

      .saved-run-tabs .q-tab {
        min-height: 52px;
        padding: 2px 18px;
        border-radius: 14px;
        border: 1px solid rgba(122, 98, 83, 0.14);
        background: rgba(255, 251, 246, 0.94);
        color: #6B5547;
        font-size: 14px !important;
        font-weight: 700;
        letter-spacing: 0.01em;
        transition: background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
      }

      .saved-run-tabs .q-tab__content {
        min-height: 100%;
        justify-content: center;
        overflow: visible;
      }

      .saved-run-tabs .q-tab__label {
        display: inline-flex;
        align-items: center;
        line-height: 1.25;
        padding-top: 1px;
      }

      .saved-run-tabs .q-tab--active {
        background: linear-gradient(135deg, #D96B1F, #B95416);
        border-color: transparent;
        color: #FFFFFF;
        box-shadow: 0 12px 24px rgba(102, 61, 35, 0.16);
      }

      .saved-run-tabs .q-tab__indicator {
        display: none;
      }

      .saved-run-tabs .q-focus-helper {
        opacity: 0 !important;
      }

      .saved-run-tabs-sticky {
        position: sticky;
        top: calc(var(--nav-height) + 12px);
        z-index: 24;
      }

      .saved-run-tab-panels > .q-panel {
        padding: 0;
      }

      .mode-advanced {

        background: var(--accent-soft);

        border: 1px solid rgba(232, 89, 12, 0.22);

        border-radius: 14px;

        padding: 12px;

      }

      .q-field__native,

      .q-field__prefix,

      .q-field__suffix {

        font-size: 16px !important;

      }

      .q-field__label {

        font-size: 14px !important;

      }

      .q-btn .q-btn__content {

        font-size: 16px !important;

      }

      .callout {

        background: rgba(255, 248, 240, 0.96);

        border-radius: 18px;

        padding: 16px;

        border: 1px solid rgba(232,89,12,0.18);

      }

      .notice-chip {
        display: inline-flex;
        align-items: center;
        width: fit-content;
        padding: 3px 8px;
        border-radius: 999px;
        background: rgba(232, 89, 12, 0.12);
        color: #B45309;
        font-size: 11px !important;
        font-weight: 700;
        letter-spacing: 0.04em;
      }

      .helper-note {
        font-size: 12px !important;
        color: rgba(31, 41, 55, 0.68);
        line-height: 1.6;
      }

      .action-link {
        font-size: 14px !important;
        font-weight: 600;
        color: var(--accent-2);
      }

      .section-eyebrow {
        font-size: 12px !important;
        font-weight: 700;
        letter-spacing: 0.04em;
        color: var(--text-muted);
      }

      .principles-card {

        background: rgba(255, 255, 255, 0.92);

        border-radius: 18px;

        padding: 14px 16px;

        border: 1px solid rgba(13, 17, 23, 0.08);

      }

      .select-sm .q-field__label,
      .select-sm .q-field__native,
      .select-sm .q-field__input {
        font-size: 13px !important;
      }

      .select-menu-sm .q-item__label {
        font-size: 13px !important;
      }

      .q-expansion-item {
        border: 1px solid var(--border);
        border-radius: 12px;
        background: var(--surface);
        overflow: hidden;
      }

      .q-expansion-item__header {
        background: var(--surface-muted);
        font-weight: 600;
      }

      .q-expansion-item--expanded .q-expansion-item__header {
        background: var(--accent-soft);
      }

      .q-expansion-item__content {
        background: var(--surface);
      }

      .print-detail-shell {
        background: rgba(255, 255, 255, 0.7);
        border: 1px solid rgba(13, 17, 23, 0.08);
        border-radius: 18px;
        padding: 14px;
      }

      .print-detail-note {
        font-size: 12px !important;
        color: rgba(13, 17, 23, 0.65);
        margin-bottom: 8px;
      }

      .print-detail-section {
        border: 1px solid rgba(13, 17, 23, 0.08);
        border-radius: 16px;
        padding: 12px 14px;
        background: #FFFFFF;
        box-shadow: none;
        break-inside: auto;
      }

      .print-detail-title {
        font-size: 18px !important;
        font-weight: 700;
        color: #0B1420;
        margin-bottom: 6px;
      }

      .print-detail-divider {
        border-top: 1px dashed rgba(13, 17, 23, 0.18);
        margin: 10px 0;
      }

      /* ---- TECHIE nav ---- */
      .hub-nav {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: var(--nav-height);
        background: var(--nav-bg);
        display: flex;
        align-items: center;
        gap: 20px;
        padding: 0 24px;
        z-index: 9999;
        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
        pointer-events: auto;
      }
      .hub-nav * {
        pointer-events: auto;
      }
      .hub-nav a {
        color: var(--nav-text);
        text-decoration: none;
        font-size: 14px;
        font-weight: 600;
        min-height: 44px;
        padding: 0 14px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        white-space: nowrap;
        transition: color 0.2s;
        border-radius: 999px;
      }
      .hub-nav a:hover {
        color: var(--nav-text-hover);
      }
      .hub-nav a.hub-nav-active {
        color: var(--nav-text-active);
        background: rgba(255,255,255,0.08);
      }
      .hub-nav a.hub-nav-home {
        color: #ffffff;
        background: linear-gradient(135deg, var(--accent), var(--accent-2));
        padding: 6px 12px;
        border-radius: 999px;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(217, 72, 15, 0.3);
      }
      .hub-nav a.hub-nav-home:hover {
        color: #ffffff;
        box-shadow: 0 6px 16px rgba(217, 72, 15, 0.38);
      }
      .hub-nav .hub-nav-sep {
        color: #4F6070;
        font-size: 12px;
        user-select: none;
      }

      /* ---- STEP スティッキーバー ---- */
      .step-track {
        position: sticky;
        top: var(--nav-height);
        z-index: 500;
        background: rgba(255, 248, 245, 0.97);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-bottom: 1px solid var(--border);
        padding: 8px 0;
        display: flex !important;
        align-items: center;
        justify-content: center;
        gap: 10px;
      }
      .step-track-item {
        font-size: 12px;
        font-weight: 700;
        padding: 5px 16px;
        border-radius: 99px;
        transition: background 0.3s ease, color 0.3s ease;
        white-space: nowrap;
      }
      .step-track-active {
        background: var(--accent);
        color: white !important;
        box-shadow: 0 3px 10px rgba(232, 89, 12, 0.28);
      }
      .step-track-done {
        background: #D1FAE5;
        color: #065F46 !important;
      }
      .step-track-pending {
        background: #F3F4F6;
        color: #9CA3AF !important;
      }

      @media (max-width: 1080px) {
        .hero-shell,
        .input-grid,
        .workspace-grid,
        .workspace-shell {
          grid-template-columns: 1fr;
        }

        .summary-rail {
          position: static;
          top: auto;
        }

        .workspace-nav {
          position: static;
          top: auto;
          padding: 14px 12px;
        }

        .app-shell {
          padding: 0 14px;
        }

        .hero-copy {
          padding: 20px;
        }

        .hero-brand-row {
          align-items: flex-start;
        }
      }

      @media (max-width: 760px) {
        .dashboard-analyze-grid {
          grid-template-columns: 1fr;
        }

        .dashboard-top-grid {
          grid-template-columns: 1fr;
        }

        .evaluation-grid,
        .evaluation-reason-grid {
          grid-template-columns: 1fr;
        }

        .dashboard-history-desktop {
          display: none;
        }

        .dashboard-history-mobile {
          display: block;
        }

        .dashboard-history-card {
          padding: 12px 12px 10px;
        }

        .dashboard-history-url {
          font-size: 14px !important;
        }

        .workspace-tabs .q-tabs__content {
          gap: 4px;
        }
      }

    </style>

    <script>
    (function(){
      var STEPS = [
        {sel:'.sticky-s1', lbl:'\u2460 URL\u5165\u529b',   done:'\u2713 URL\u5165\u529b'},
        {sel:'.sticky-s2', lbl:'\u2461 \u8a73\u7d30\u8a2d\u5b9a', done:'\u2713 \u8a73\u7d30\u8a2d\u5b9a'},
        {sel:'.sticky-s3', lbl:'\u2462 \u5206\u6790\u7d50\u679c', done:'\u2713 \u5206\u6790\u7d50\u679c'},
      ];
      var scrollStep = 0;
      var STICKY_H = 80;  // nav(40px) + step-track(padding 16px + item 10px + font ~14px ≈ 40px)

      function refreshBar() {
        STEPS.forEach(function(s, i) {
          var el = document.querySelector(s.sel);
          if (!el) return;
          if (el.classList.contains('step-track-done')) return;
          el.classList.remove('step-track-active', 'step-track-pending');
          el.classList.add(i === scrollStep ? 'step-track-active' : 'step-track-pending');
          el.textContent = s.lbl;
        });
      }

      var cards = [];

      function calcScrollStep() {
        var newActive = 0;
        for (var i = 0; i < cards.length - 1; i++) {
          if (!cards[i]) continue;
          var bottom = cards[i].getBoundingClientRect().bottom;
          if (bottom <= STICKY_H + 8) { newActive = i + 1; }
        }
        if (newActive !== scrollStep) {
          scrollStep = newActive;
          refreshBar();
        }
      }

      function initScrollSpy() {
        var sels = ['.step-card-1', '.step-card-2', '.step-card-3'];
        cards = sels.map(function(s){ return document.querySelector(s); });
        if (cards.some(function(c){ return !c; })) {
          setTimeout(initScrollSpy, 250);
          return;
        }
        window.addEventListener('scroll', calcScrollStep, { passive: true });
        calcScrollStep();
        refreshBar();
      }

      setTimeout(initScrollSpy, 450);
    })();
    </script>

    """,

    shared=True,

)

def legacy_main_page() -> None:
    main_page()


def _render_shared_nav() -> None:
    ui.html(
        f'''
            <nav class="hub-nav">
              <a href="{HUB_URL}" class="hub-nav-home">HOME</a>
              <span class="hub-nav-sep">|</span>
              <a href="{KOTOMAKE_URL}">発信作成</a>
              <span class="hub-nav-sep">|</span>
              <a href="{KOTOMEGANE_URL}">見え方観測</a>
              <span class="hub-nav-sep">|</span>
              <a href="{KOTOMIGAKI_URL}" class="hub-nav-active">サイト改善</a>
            </nav>
        ''',
        sanitize=HTML_SANITIZER.sanitize,
    )


def _render_dashboard_brand_header() -> None:
    with ui.card().classes("card dashboard-brand-strip w-full"):
        with ui.row().classes("hero-brand-row w-full items-center justify-between gap-4 flex-wrap"):
            with ui.row().classes("items-center gap-4 min-w-[280px]"):
                ui.image("/static/logo_mark.svg").classes("hero-logo")
                with ui.column().classes("hero-brand-copy"):
                    ui.label("TECHIE / コトミガキ").classes("hero-service-note")
                    ui.label("分析後は保存され、履歴比較やCSV出力までこの画面で続けられます。").classes("card-hint")
            ui.link("見え方観測へ", KOTOMEGANE_URL).classes("dashboard-utility-link")


def _render_detail_brand_header(url: str) -> None:
    with ui.card().classes("card p-5 w-full"):
        ui.label("TECHIE").classes("hero-kicker")
        with ui.row().classes("items-center justify-between w-full gap-4 flex-wrap"):
            with ui.column().classes("gap-1 min-w-[280px]"):
                ui.label("コトミガキ | サイト改善").classes("card-title")
                ui.label(url).classes("card-sub break-all")
            with ui.row().classes("gap-2 flex-wrap"):
                ui.link("見え方観測へ", KOTOMEGANE_URL).classes("secondary-btn")
                ui.link("ダッシュボードへ戻る", "/").classes("secondary-btn")


@ui.page("/")
def main_page() -> None:
    search_state = {"value": ""}
    sort_state = {"value": "analyzed_at"}
    descending_state = {"value": True}
    current_rows: Dict[str, List[Dict[str, Any]]] = {"value": []}

    with ui.column().classes("app-shell gap-5"):
        _render_shared_nav()

        with ui.card().classes("card dashboard-analyze-card p-6 w-full"):
            with ui.row().classes("items-center justify-between w-full gap-3 flex-wrap"):
                with ui.column().classes("gap-1"):
                    ui.label("URLを入れて分析").classes("card-title")
                    ui.label("最初に必要なのはURLだけです。比較や条件は必要なときだけ開けます。").classes("card-hint")

            with ui.element("div").classes("dashboard-analyze-grid w-full mt-4"):
                with ui.column().classes("dashboard-analyze-form w-full min-w-0"):
                    url_input = ui.input(
                        "URL",
                        placeholder="https://example.com",
                    ).classes("w-full analysis-url-input").props("input-debounce=0")
                    url_error_label = ui.label("").classes("text-sm text-negative")
                    url_error_label.visible = False

                    competitor_expansion = ui.expansion("比較サイト", icon="add_link", value=False).classes("w-full compact-expansion")
                    with competitor_expansion:
                        competitor_input = ui.input(
                            "比較URL",
                            placeholder="https://competitor.example.com",
                        ).classes("w-full analysis-competitor-input").props("input-debounce=0")
                        competitor_error_label = ui.label("").classes("text-sm text-negative")
                        competitor_error_label.visible = False

                    settings_expansion = ui.expansion("条件", icon="tune", value=False).classes("w-full compact-expansion")
                    with settings_expansion:
                        industry_select = ui.select(
                            {
                                option: INDUSTRY_OPTION_LABELS.get(option, option)
                                for option in [
                                    "自動判定",
                                    "化粧品・美容",
                                    "健康食品・サプリメント",
                                    "医療・クリニック",
                                    "不動産・住宅",
                                    "金融・保険",
                                    "人材・求人",
                                    "教育・スクール",
                                    "法律・士業",
                                    "IT・SaaS",
                                    "飲食・フード",
                                    "小売・EC",
                                    "製造業",
                                    "建設・建築",
                                    "その他",
                                ]
                            },
                            value="自動判定",
                            label="業界",
                        ).classes("w-full select-sm")
                        platform_select = ui.select(
                            PLATFORM_OPTION_LABELS,
                            value="自動判定",
                            label="作成サービス",
                        ).classes("w-full select-sm")
                        url_type_select = ui.select(
                            URL_TYPE_OPTION_LABELS,
                            value="自動判定",
                            label="種別",
                        ).classes("w-full select-sm")
                        ui.label("検索 / AI").classes("input-label")
                        balance_slider = ui.slider(min=0, max=100, value=50, step=5).props("label-always")

                with ui.column().classes("dashboard-analyze-side dashboard-side-panel gap-2"):
                    ui.label("START").classes("dashboard-side-kicker")
                    ui.label("この画面でやること").classes("dashboard-side-title")
                    ui.label("1件のURLを入れて分析を開始します。").classes("dashboard-side-point")
                    ui.label("結果は保存され、あとで比較やCSV出力に進めます。").classes("dashboard-side-point")
                    ui.label("所要時間の目安は1〜3分です。").classes("dashboard-side-point")

            analyze_button = ui.button("分析する").props("unelevated no-caps color=orange-8 text-color=white").classes("primary-btn w-full mt-4").style(
                "background: linear-gradient(135deg, #D96B1F, #B95416); color: #FFFFFF; border: none;"
            )
            auto_open_state = {"value": True}
            with ui.row().classes("items-center justify-between gap-3 flex-wrap mt-2"):
                auto_open_toggle = ui.switch("保存後に開く", value=True).props("dense color=orange-8")

            with ui.row().classes("dashboard-status-bar w-full items-center justify-between gap-3 flex-wrap mt-3"):
                status_label = ui.label("").classes("card-sub")
                with ui.row().classes("items-center gap-3"):
                    stay_on_page_button = ui.button("今は移動しない", color=None).props("no-caps").classes("secondary-btn").style(
                        "background: rgba(255, 251, 246, 0.96); color: #7A3A16; border: 1px solid rgba(122, 98, 83, 0.18);"
                    )
                    stay_on_page_button.visible = False
                    loading = ui.spinner(size="md", color="orange-8")
                    token_usage_label = ui.label("").classes("text-xs text-gray-400 opacity-70")
                    saved_run_link = ui.link("", "#").classes("secondary-btn")
                    saved_run_link.visible = False
            progress_label = ui.label("").classes("card-sub text-sm mt-2")
            progress_bar = ui.linear_progress(value=0, show_value=False, color="orange-8").classes("w-full mt-1")
            progress_bar.visible = False

        _render_dashboard_brand_header()

        loading.visible = False
        token_usage_label.visible = False

        def _set_input_error(target, message: Optional[str]) -> None:
            target.text = message or ""
            target.visible = bool(message)

        def _set_auto_open_preference(enabled: bool, *, announce: bool = False) -> None:
            auto_open_state["value"] = bool(enabled)
            stay_on_page_button.visible = state.busy and auto_open_state["value"]
            if announce:
                if auto_open_state["value"]:
                    status_label.text = "完了後は保存結果を自動で開く設定に戻しました。"
                else:
                    status_label.text = "分析は続行します。完了後はこの画面にとどまります。"

        def _refresh_analyze_button_state() -> None:
            if state.busy:
                analyze_button.disable()
                return
            normalized_url, url_error = _validate_analysis_input_url(
                url_input.value or "",
                label="対象URL",
                required=bool((url_input.value or "").strip()),
            )
            normalized_competitor_url, competitor_error = _validate_analysis_input_url(
                competitor_input.value or "",
                label="比較サイト",
                required=False,
            )
            if not url_error and not competitor_error and normalized_url and normalized_competitor_url:
                if normalized_url == normalized_competitor_url:
                    competitor_error = "比較サイトは対象URLと別のURLを入力してください。"
            _set_input_error(url_error_label, url_error)
            _set_input_error(competitor_error_label, competitor_error)
            analyze_button.enable()

        def _bind_analysis_readiness_watchers(target) -> None:
            target.on("update:model-value", lambda _event: _refresh_analyze_button_state())
            target.on("change", lambda _event: _refresh_analyze_button_state())

        dashboard_progress_steps = [
            "URL取得",
            "本文解析",
            "検索向け評価",
            "AI検索向け評価",
            "表示アドバイス確認",
            "レポート整理",
            "競合比較",
            "保存",
        ]

        def update_dashboard_progress_label() -> None:
            if state.progress_stage == "完了":
                progress_bar.visible = True
                progress_label.text = _build_completion_progress_text(auto_open_state["value"])
                progress_bar.value = 1.0
                return
            if not state.busy or not state.progress_started_at:
                progress_label.text = ""
                progress_bar.value = 0
                progress_bar.visible = False
                return
            progress_bar.visible = True
            if state.progress_stage:
                pct = int(max(0.0, min(state.progress_percent, 1.0)) * 100)
                detail = f" - {state.progress_detail}" if state.progress_detail else ""
                progress_label.text = f"進捗: {state.progress_stage}{detail} ({pct}%)"
                progress_bar.value = max(0.0, min(state.progress_percent, 1.0))
                return
            elapsed = (datetime.now() - state.progress_started_at).total_seconds()
            idx = min(int(elapsed / 20), len(dashboard_progress_steps) - 1)
            progress_label.text = f"進捗: {dashboard_progress_steps[idx]}（目安: 1〜3分）"
            progress_bar.value = (idx + 1) / len(dashboard_progress_steps)

        page_client = ui.context.client
        dashboard_progress_disconnect = asyncio.Event()

        async def _sync_latest_analysis_inputs_from_dom() -> tuple[str, str]:
            try:
                latest_values = await page_client.run_javascript(
                    """
                    (() => {
                        const readValue = (selector) => {
                            const root = document.querySelector(selector);
                            if (!root) return '';
                            const input = root.matches('input, textarea') ? root : root.querySelector('input, textarea');
                            return input ? String(input.value || '') : '';
                        };
                        return {
                            url: readValue('.analysis-url-input'),
                            competitor: readValue('.analysis-competitor-input'),
                        };
                    })()
                    """,
                    timeout=2.0,
                )
            except Exception as exc:
                logger.debug("dashboard input同期をスキップ: %s", exc)
                return str(url_input.value or ""), str(competitor_input.value or "")

            latest_url = str((latest_values or {}).get("url") or url_input.value or "")
            latest_competitor = str((latest_values or {}).get("competitor") or competitor_input.value or "")
            url_input.value = latest_url
            competitor_input.value = latest_competitor
            return latest_url, latest_competitor

        def _safe_dashboard_ui_refresh(refresh_fn, stop_event: asyncio.Event) -> bool:
            if stop_event.is_set() or not page_client.has_socket_connection:
                stop_event.set()
                return False
            try:
                refresh_fn()
                return True
            except RuntimeError as exc:
                logger.debug("dashboard client切断後のUI更新を停止: %s", exc)
                stop_event.set()
                return False

        async def _run_dashboard_progress_loop() -> None:
            try:
                while not dashboard_progress_disconnect.is_set():
                    if not _safe_dashboard_ui_refresh(update_dashboard_progress_label, dashboard_progress_disconnect):
                        break
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                return

        dashboard_progress_task = asyncio.create_task(_run_dashboard_progress_loop())
        page_client.on_disconnect(lambda: dashboard_progress_disconnect.set())
        page_client.on_disconnect(lambda: dashboard_progress_task.cancel())

        with ui.card().classes("card dashboard-toolbar-card p-5 w-full"):
            with ui.row().classes("w-full items-end gap-3 flex-wrap"):
                search_input = ui.input("履歴検索", placeholder="URLで検索").classes("flex-1 min-w-[260px]")
                sort_select = ui.select(
                    {
                        "analyzed_at": "新しい順",
                        "aio_score": "AI認識順",
                        "seo_score": "SEO順",
                        "total_issues": "課題数順",
                    },
                    value="analyzed_at",
                    label="並び替え",
                ).classes("w-[180px]")
                sort_button = ui.button("降順", icon="south", color=None).props("no-caps").classes("secondary-btn").style(
                    "background: rgba(255, 251, 246, 0.96); color: #7A3A16; border: 1px solid rgba(122, 98, 83, 0.18);"
                )
                export_button = ui.button("履歴CSV", color=None).props("no-caps").classes("secondary-btn").style(
                    "background: rgba(255, 251, 246, 0.96); color: #7A3A16; border: 1px solid rgba(122, 98, 83, 0.18);"
                )

            @ui.refreshable
            def dashboard_section() -> None:
                render_history_table(current_rows["value"], on_open_run=lambda run_id: ui.navigate.to(f"/runs/{run_id}"))

            def _load_dashboard_rows() -> List[Dict[str, Any]]:
                rows = build_history_rows(
                    get_history(
                        limit=50,
                        search=search_state["value"] or None,
                        sort_by=sort_state["value"],
                        descending=descending_state["value"],
                    )
                )
                current_rows["value"] = rows
                return rows

            def _refresh_dashboard_views() -> None:
                _load_dashboard_rows()
                dashboard_section.refresh()

            def _refresh_dashboard_from_inputs() -> None:
                search_state["value"] = search_input.value or ""
                sort_state["value"] = sort_select.value or "analyzed_at"
                _refresh_dashboard_views()

            def _toggle_sort() -> None:
                descending_state["value"] = not descending_state["value"]
                sort_button.text = "降順" if descending_state["value"] else "昇順"
                sort_button.props(f"icon={'south' if descending_state['value'] else 'north'}")
                _refresh_dashboard_views()

            def _export_history() -> None:
                output_path = export_history_csv(current_rows["value"])
                ui.download(output_path, filename=output_path.name, media_type="text/csv")

            async def run_analysis() -> None:
                if not await _ensure_usage_credit_available("kotomigaki"):
                    return
                latest_url, latest_competitor_url = await _sync_latest_analysis_inputs_from_dom()
                normalized_url, url_error = _validate_analysis_input_url(
                    latest_url,
                    label="対象URL",
                    required=True,
                )
                normalized_competitor_url, competitor_error = _validate_analysis_input_url(
                    latest_competitor_url,
                    label="比較サイト",
                    required=False,
                )
                if not url_error and not competitor_error and normalized_url and normalized_competitor_url:
                    if normalized_url == normalized_competitor_url:
                        competitor_error = "比較サイトは対象URLと別のURLを入力してください。"
                _set_input_error(url_error_label, url_error)
                _set_input_error(competitor_error_label, competitor_error)
                if url_error or competitor_error:
                    status_label.text = url_error or competitor_error or ""
                    return
                url = normalized_url
                url_input.value = normalized_url
                url_input.update()
                competitor_input.value = normalized_competitor_url
                competitor_input.update()

                state.busy = True
                state.progress_started_at = datetime.now()
                _push_progress_update("分析中", 0.5, "完了までこのままお待ちください")
                _refresh_analyze_button_state()
                stay_on_page_button.visible = auto_open_state["value"]
                loading.visible = True
                token_usage_label.visible = False
                saved_run_link.visible = False
                status_label.text = "分析を開始しました。進捗を表示します。"
                update_dashboard_progress_label()
                progress_label.update()
                progress_bar.update()
                status_label.update()
                loading.update()
                await asyncio.sleep(0.05)

                try:
                    analyzer = ensure_analyzer()
                    industry_value = industry_select.value or "自動判定"
                    platform_value = platform_select.value or "自動判定"
                    url_type_value = url_type_select.value or "自動判定"
                    goal_value = "自動判定"
                    balance_value = int(balance_slider.value or 50)

                    def handle_progress(stage: str, percent: float, detail: Optional[str] = None) -> None:
                        # Keep the live dashboard simple: 50% while running, 100% after saved.
                        # Detailed analyzer stages can arrive from blocking worker threads and
                        # otherwise make the text/bar appear out of sync for users.
                        return

                    state.results = await run.io_bound(
                        execute_primary_analysis,
                        analyzer,
                        url,
                        industry_value,
                        balance_value,
                        True,
                        platform_value,
                        url_type_value,
                        goal_value,
                        handle_progress,
                    )

                    competitor_url = normalized_competitor_url
                    state.competitor_results = None
                    state.competitor_action_advice = None
                    state.competitor_blocked = None
                    state.competitor_error = None
                    if competitor_url:
                        _push_progress_update("競合比較", 0.95, "競合URLを解析中")
                        competitor_outcome = await run.io_bound(
                            execute_competitor_analysis,
                            competitor_url,
                            industry_value,
                            balance_value,
                            True,
                            goal_value,
                            state.results,
                        )
                        state.competitor_results = competitor_outcome.results
                        state.competitor_action_advice = competitor_outcome.action_advice
                        state.competitor_blocked = competitor_outcome.blocked
                        state.competitor_error = competitor_outcome.error

                    _push_progress_update("保存", 0.98, "履歴へ保存")
                    run_id = persist_analysis_run(
                        url,
                        state.results,
                        competitor_results=state.competitor_results,
                        competitor_action_advice=state.competitor_action_advice,
                        competitor_blocked=state.competitor_blocked,
                        competitor_error=state.competitor_error,
                    )
                    state.last_run_id = run_id
                    _refresh_dashboard_views()
                    credit_debited = await _consume_usage_credit_after_success(
                        service_key="kotomigaki",
                        action_key="analyze",
                        attempt_id=str(run_id or f"analysis:{url}:{int(state.progress_started_at.timestamp())}"),
                    )
                    _push_progress_update("完了", 1.0, "保存済みワークスペースへ移動")

                    try:
                        token_usage_text = build_token_usage_text(analyzer.token_tracker.get_summary())
                        if token_usage_text:
                            token_usage_label.text = token_usage_text
                            token_usage_label.visible = True
                    except Exception as token_exc:
                        print(f"[WARNING] トークン使用量取得エラー: {token_exc}")

                    if run_id:
                        run_path = f"/runs/{run_id}"
                        saved_run_link.set_text(f"保存結果 #{run_id} を開く")
                        saved_run_link._props["href"] = run_path
                        saved_run_link.update()
                        saved_run_link.visible = True
                        status_label.text = (
                            _build_saved_run_status_text(auto_open_state["value"])
                            if credit_debited
                            else "分析は完了して保存しましたが、クレジット消費を確認できませんでした。管理者へ連絡してください。"
                        )
                        logger.info(
                            "保存完了: run_id=%s socket_connected_before=%s",
                            run_id,
                            page_client.has_socket_connection,
                        )
                        if auto_open_state["value"] and credit_debited:
                            try:
                                await page_client.connected(timeout=8.0)
                                logger.info(
                                    "保存後遷移送信: run_id=%s socket_connected_after=%s",
                                    run_id,
                                    page_client.has_socket_connection,
                                )
                                page_client.open(run_path)
                            except Exception as nav_exc:
                                logger.warning("保存後遷移を保留: run_id=%s reason=%s", run_id, nav_exc)
                    else:
                        status_label.text = "分析は完了しましたが、保存に失敗しました。"

                except UnsafeURLError as exc:
                    logger.error("分析エラー: %s", exc, exc_info=True)
                    status_label.text = "安全上、指定URLを取得できませんでした。"
                except ContentTooLargeError as exc:
                    logger.error("分析エラー: %s", exc, exc_info=True)
                    max_mb = round(exc.max_bytes / (1024 * 1024), 1) if hasattr(exc, "max_bytes") else 10
                    status_label.text = f"対象ページのHTMLが大きすぎて解析を中断しました（上限 {max_mb}MB）。"
                except TooManyRedirectsError as exc:
                    logger.error("分析エラー: %s", exc, exc_info=True)
                    status_label.text = "リダイレクトが多すぎて取得できませんでした。"
                except ScrapeBlockedError as exc:
                    logger.error("分析エラー: %s", exc, exc_info=True)
                    status_label.text = f"取得制限のため分析できませんでした: {exc.reason}"
                except Exception as exc:
                    logger.error("分析エラー: %s", exc, exc_info=True)
                    status_label.text = _build_user_error_message(str(exc))
                finally:
                    state.busy = False
                    _refresh_analyze_button_state()
                    stay_on_page_button.visible = False
                    loading.visible = False
                    if state.progress_stage != "完了":
                        progress_bar.visible = False
                    if state.progress_stage == "完了":
                        async def delayed_progress_reset() -> None:
                            await asyncio.sleep(1.5)
                            _reset_progress_state()
                        asyncio.create_task(delayed_progress_reset())
                    else:
                        _reset_progress_state()

            analyze_button.on("click", run_analysis)
            auto_open_toggle.on("update:model-value", lambda event: _set_auto_open_preference(bool(event.value), announce=state.busy))
            stay_on_page_button.on("click", lambda: _set_auto_open_preference(False, announce=True))
            _bind_analysis_readiness_watchers(url_input)
            _bind_analysis_readiness_watchers(competitor_input)
            _bind_analysis_readiness_watchers(industry_select)
            _bind_analysis_readiness_watchers(platform_select)
            _bind_analysis_readiness_watchers(url_type_select)
            _bind_analysis_readiness_watchers(balance_slider)

            search_input.on("update:model-value", lambda _event: _refresh_dashboard_from_inputs())
            sort_select.on("update:model-value", lambda _event: _refresh_dashboard_from_inputs())
            sort_button.on("click", _toggle_sort)
            export_button.on("click", _export_history)
            _refresh_dashboard_views()
            _refresh_analyze_button_state()


@ui.page("/runs/{run_id}")
def run_detail_page(run_id: str) -> None:
    try:
        run_id_int = int(run_id)
    except (TypeError, ValueError):
        with ui.column().classes("app-shell"):
            _render_shared_nav()
            with ui.card().classes("card p-6 w-full"):
                ui.label("無効な run_id です。").classes("card-title")
        return

    bundle = load_saved_run_bundle(run_id_int)
    with ui.column().classes("app-shell gap-5"):
        _render_shared_nav()
        if not bundle:
            with ui.card().classes("card p-6 w-full"):
                ui.label("保存済み分析が見つかりません。").classes("card-title")
                ui.link("ダッシュボードへ戻る", "/").classes("secondary-btn")
            return

        run_row = bundle.get("run") or {}
        _render_detail_brand_header(str(run_row.get("url") or ""))

        def _export_priority_actions() -> None:
            output_path = export_priority_actions_csv(bundle.get("snapshot") or {}, run_row)
            ui.download(output_path, filename=output_path.name, media_type="text/csv")

        def _export_detailed_markdown() -> None:
            output_path = export_detailed_markdown_report(bundle)
            ui.download(output_path, filename=output_path.name, media_type="text/markdown")

        def _export_detailed_docx() -> None:
            try:
                output_path = export_detailed_docx_report(bundle)
            except Exception as exc:
                logger.error("DOCX report export failed: %s", exc, exc_info=True)
                ui.notify("Wordレポートの出力に失敗しました。環境を確認してから再実行してください。", type="negative")
                return
            ui.download(
                output_path,
                filename=output_path.name,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

        with ui.row().classes("w-full justify-between items-center gap-3 flex-wrap"):
            with ui.column().classes("gap-1"):
                ui.label("レポート出力").classes("section-eyebrow")
                ui.label("完成版レポートをMarkdownまたはWord形式で保存できます。").classes("card-hint")
            with ui.row().classes("gap-3 flex-wrap justify-end"):
                with ui.button("レポート出力", icon="download", color=None).props("unelevated no-caps").classes("primary-btn report-export-btn").style(
                    "min-width: 178px; min-height: 48px; font-weight: 800;"
                ):
                    with ui.menu().props('anchor="bottom right" self="top right"'):
                        ui.menu_item("Markdown（.md）", on_click=_export_detailed_markdown)
                        ui.menu_item("Word（.docx）", on_click=_export_detailed_docx)
            ui.button("優先アクションCSV", on_click=_export_priority_actions, color=None).props("no-caps").classes("secondary-btn").style(
                "background: rgba(255, 251, 246, 0.96); color: #7A3A16; border: 1px solid rgba(122, 98, 83, 0.18);"
            )

        render_saved_run_workspace(bundle)

def run_app(host: str = "127.0.0.1", port: Optional[int] = None) -> None:

    final_port = port or int(os.environ.get("PORT", 8501))
    headless = os.environ.get("HEADLESS", "").lower() in ("1", "true", "yes")

    def open_browser():
        if not headless:
            webbrowser.open(f"http://{host}:{final_port}")

    app.on_startup(open_browser)

    # 静的ファイル設定
    STATIC_DIR = Path(__file__).parent / "static"
    STATIC_DIR.mkdir(exist_ok=True)
    app.add_static_files("/static", str(STATIC_DIR))

    ui.run(
        host=host,
        port=final_port,
        title="コトミガキ | TECHIE",
        favicon=str(STATIC_DIR / "favicon_v2.png"),
        storage_secret=os.environ.get("NICEGUI_STORAGE_SECRET")
        or os.environ.get("SESSION_SECRET")
        or "techie-nicegui-storage-secret",
        reload=False,
        show=False,
    )

if __name__ in {"__main__", "__mp_main__"}:

    run_app()
