# -*- coding: utf-8 -*-
"""Build split accessibility improvement actions for UI and engineer surfaces.

Rule-based scoring and ordering are fixed here. Optional LLM formatting may
only rewrite display copy; it must not add, remove, or reorder actions.
"""

from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from core.aio_suggestions import sanitize_untrusted_prompt_text
from core.config import config
from core.env_keys import resolve_env_var
from core.llm_responses_client import call_structured


RULESET_VERSION = "accessibility-action-builder-v1"
PROMPT_VERSION = "accessibility-action-copy-v1"
DEFAULT_LLM_MODEL = os.getenv("OPENAI_ACCESSIBILITY_ACTION_MODEL", "gpt-5.4-nano")
DEFAULT_REASONING_EFFORT = os.getenv("OPENAI_ACCESSIBILITY_REASONING_EFFORT", "low")
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_PARALLEL = 3

_REASONING_EFFORTS = {"none", "low"}
_STATUS_URGENCY = {
    "needs_work": "高",
    "warning": "中",
    "ok": "低",
}
_EFFORT_BY_GROUP = {
    "image_alt": "低",
    "interactive_names": "低",
    "form_labels": "低",
    "h1": "低",
    "heading_hierarchy": "中",
    "landmarks": "中",
    "html_lang": "低",
    "title": "低",
    "iframe_titles": "低",
    "color_contrast": "中",
    "zoom_scaling": "低",
    "aria_semantics": "中",
    "keyboard_focus": "中",
    "screen_reader_structure": "中",
}

_ENGINEER_WORK_BY_GROUP = {
    "image_alt": "画像の用途を確認し、内容画像には説明的なalt、装飾画像には空のaltを設定してください。",
    "interactive_names": "テキスト、aria-label、aria-labelledby、title、画像altのいずれかで操作目的が取得できるようにしてください。",
    "form_labels": "label要素、aria-label、aria-labelledby、titleのいずれかで入力目的が取得できるようにしてください。",
    "h1": "ページ主題を表すh1を1つに整理し、ロゴや装飾だけがh1になっていないか確認してください。",
    "heading_hierarchy": "見出しレベルがh1、h2、h3の順に続くように整理し、レベルの飛びを解消してください。",
    "landmarks": "header、nav、main、footerなどで主要領域を明示し、本文をmain内に収めてください。",
    "html_lang": "html要素へページ言語を示すlang属性を設定してください。",
    "title": "ページ固有のtitle要素を設定し、ブラウザタブ名と検索結果で内容が分かる状態にしてください。",
    "iframe_titles": "地図、動画、予約フォームなどのiframeへ内容が分かるtitle属性を設定してください。",
    "color_contrast": "検出された文字色と背景色の組み合わせを見直し、通常文字は4.5:1以上を目安に再確認してください。",
    "zoom_scaling": "viewport設定から拡大制限を外し、スマートフォンでピンチズームできる状態にしてください。",
    "aria_semantics": "roleとaria属性の組み合わせを確認し、不要なARIAを削除するか正しいHTML要素へ置き換えてください。",
    "keyboard_focus": "Tab順序、Enter操作、フォーカス表示を実ブラウザで確認し、主要導線をキーボードだけで完了できるようにしてください。",
    "screen_reader_structure": "見出し、ランドマーク、操作部品名を整理し、読み上げの一覧でページ構造と次の操作が分かる状態にしてください。",
}

_AUDIENCE_COPY_BY_GROUP = {
    "image_alt": {
        "action": "商品写真や説明画像が、見えない環境でも内容として伝わるか見直してください。",
        "review_area": "商品画像・サービス説明画像",
        "handoff_to": "Web制作担当またはCMS更新担当",
        "impact": "画像の意味が検索・AI回答・読み上げに伝わりやすくなります。",
        "confirmation": "主要な画像に説明が付いている状態か、制作担当へ確認してください。",
    },
    "interactive_names": {
        "action": "アイコンだけのボタンや画像リンクが、何をする操作か分かる状態か見直してください。",
        "review_area": "メニュー、問い合わせ、購入、予約などの操作ボタン",
        "handoff_to": "Web制作担当またはフロントエンド担当",
        "impact": "利用者が迷わず操作でき、AIや読み上げにも導線の意味が伝わりやすくなります。",
        "confirmation": "主要ボタンの目的を読み上げや検査ツールで判別できるか確認してください。",
    },
    "form_labels": {
        "action": "入力欄ごとに、何を入力する欄か分かる表示になっているか見直してください。",
        "review_area": "問い合わせフォーム、検索欄、申込フォーム",
        "handoff_to": "フォーム管理担当またはWeb制作担当",
        "impact": "入力ミスや離脱を減らし、読み上げ利用者にもフォームの目的が伝わります。",
        "confirmation": "フォームの各項目名が画面と検査結果の両方で確認できるか見てください。",
    },
    "h1": {
        "action": "ページで一番伝えたい主題が、見出しとして明確に伝わるか見直してください。",
        "review_area": "ページ冒頭の大見出し",
        "handoff_to": "コンテンツ担当またはWeb制作担当",
        "impact": "検索エンジン、AI、読み上げ機能がページのテーマをつかみやすくなります。",
        "confirmation": "ページごとの主題が1つに絞れているか確認してください。",
    },
    "heading_hierarchy": {
        "action": "見出しだけを読んでもページの流れが分かるように、章立てを見直してください。",
        "review_area": "本文見出し、FAQ見出し、サービス説明見出し",
        "handoff_to": "コンテンツ担当またはWeb制作担当",
        "impact": "利用者もAIも、ページ内の情報の順番を理解しやすくなります。",
        "confirmation": "見出し一覧を確認し、話の順番が自然につながるか見てください。",
    },
    "landmarks": {
        "action": "ヘッダー、メニュー、本文、フッターの境界が分かる構成か見直してください。",
        "review_area": "ページ全体のレイアウト構造",
        "handoff_to": "Web制作担当またはテーマ開発担当",
        "impact": "本文とナビゲーションの場所が明確になり、読み上げやAIが構造を把握しやすくなります。",
        "confirmation": "本文領域とメニュー領域が検査ツールで区別できるか確認してください。",
    },
    "html_lang": {
        "action": "ページの主な言語が正しく伝わる設定になっているか見直してください。",
        "review_area": "サイト全体の言語設定",
        "handoff_to": "Web制作担当またはCMS設定担当",
        "impact": "読み上げの発音や検索エンジンの言語理解が安定します。",
        "confirmation": "日本語ページとして認識される設定になっているか制作担当へ確認してください。",
    },
    "title": {
        "action": "ブラウザタブや検索結果に出るページ名が、ページ固有の内容を表しているか見直してください。",
        "review_area": "ページ名、検索結果タイトル",
        "handoff_to": "SEO担当またはCMS更新担当",
        "impact": "検索結果やAI要約でページ内容が伝わりやすくなります。",
        "confirmation": "同じタイトルの使い回しがないか確認してください。",
    },
    "iframe_titles": {
        "action": "地図、動画、予約フォームなどの埋め込み枠が、何の内容か分かる状態か見直してください。",
        "review_area": "地図・動画・予約フォームなどの埋め込み",
        "handoff_to": "Web制作担当",
        "impact": "読み上げ利用者にも埋め込み内容の役割が伝わりやすくなります。",
        "confirmation": "埋め込みごとの内容名が検査結果で確認できるか見てください。",
    },
    "color_contrast": {
        "action": "文字色と背景色が薄すぎず、屋外や小さい画面でも読めるか見直してください。",
        "review_area": "本文、ボタン、メニュー、注記",
        "handoff_to": "デザイン担当またはWeb制作担当",
        "impact": "読みづらさによる離脱を減らし、重要な案内を見落としにくくします。",
        "confirmation": "検出された箇所の配色をデザイン担当へ渡し、再検査してください。",
    },
    "zoom_scaling": {
        "action": "スマートフォンで文字や画面を拡大して読める状態か見直してください。",
        "review_area": "スマートフォン表示",
        "handoff_to": "Web制作担当",
        "impact": "小さい文字を拡大して読む人の閲覧負担を下げます。",
        "confirmation": "実機またはブラウザで拡大できるか確認してください。",
    },
    "aria_semantics": {
        "action": "画面部品の意味や状態が、読み上げでも誤解なく伝わるか見直してください。",
        "review_area": "メニュー、タブ、開閉部品、独自UI",
        "handoff_to": "フロントエンド担当",
        "impact": "見た目では分かる操作でも、読み上げ利用者に正しく伝わりやすくなります。",
        "confirmation": "検査で指摘された部品をフロントエンド担当へ渡してください。",
    },
    "keyboard_focus": {
        "action": "マウスなしでも主要な問い合わせ・購入・予約導線を操作できるか見直してください。",
        "review_area": "主要リンク、ボタン、フォーム",
        "handoff_to": "フロントエンド担当またはQA担当",
        "impact": "キーボード操作の利用者や一時的に細かい操作が難しい人も完了しやすくなります。",
        "confirmation": "Tabキーだけで主要導線を進めるか確認してください。",
    },
    "screen_reader_structure": {
        "action": "読み上げでも現在地と次の操作が分かるページ構造か見直してください。",
        "review_area": "見出し、主要領域、操作部品名",
        "handoff_to": "Web制作担当またはQA担当",
        "impact": "読み上げ利用者とAIの両方が、ページの意味と導線を理解しやすくなります。",
        "confirmation": "見出し一覧と操作部品名を検査結果で確認してください。",
    },
}

ACTION_COPY_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["title", "action", "reason", "verification"],
    "properties": {
        "title": {"type": "string", "maxLength": 80},
        "action": {"type": "string", "maxLength": 220},
        "reason": {"type": "string", "maxLength": 180},
        "verification": {"type": "string", "maxLength": 180},
    },
}


def _safe_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _safe_int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _json_for_hash(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except (TypeError, ValueError):
        return str(value)


def _resolve_html_hash(site_health: Dict[str, Any], raw: Dict[str, Any], html: Optional[str]) -> str:
    explicit_hash = _safe_text(
        (site_health or {}).get("html_hash")
        or ((site_health or {}).get("accessibility") or {}).get("html_hash")
        or raw.get("html_hash")
    )
    if explicit_hash:
        return explicit_hash
    source = html if html is not None else _json_for_hash(raw.get("issue_groups") or raw)
    return hashlib.sha256(str(source or "").encode("utf-8")).hexdigest()


def _impact_from_group(group: Dict[str, Any]) -> str:
    status = _safe_text(group.get("status"))
    weight = _safe_int(group.get("weight"))
    affected_count = _safe_int(group.get("affected_count"))
    ratio = _safe_float(group.get("ratio"))
    if status == "needs_work" or weight >= 12 and affected_count >= 1 and ratio < 0.7:
        return "高"
    if status == "warning" or affected_count > 0:
        return "中"
    return "低"


def _priority_score(group: Dict[str, Any]) -> int:
    weight = _safe_int(group.get("weight"))
    affected_count = _safe_int(group.get("affected_count"))
    impact_bonus = {"高": 1000, "中": 500, "低": 0}.get(_impact_from_group(group), 0)
    return impact_bonus + (weight * 10) + min(affected_count, 99)


def _priority_sort_key(group: Dict[str, Any]) -> tuple[int, int, int, str]:
    return (
        -_priority_score(group),
        -_safe_int(group.get("weight")),
        -_safe_int(group.get("affected_count")),
        _safe_text(group.get("id")),
    )


ACTION_TEMPLATES: Dict[str, Dict[str, str]] = {
    "image_alt": {
        "title": "画像に内容が分かる説明文を入れる",
        "action": "商品画像・サービス説明画像に、何が写っているか分かるaltを入れてください。装飾だけの画像は空のaltにします。",
        "target": "img alt",
        "reason": "検索エンジン、AI、読み上げ機能が画像の内容を理解しやすくなります。",
        "verification": "主要画像を右クリックしてHTMLを確認し、<img>にaltが入っているか見ます。読み上げ確認では画像の意味が伝わるかを確認します。",
    },
    "interactive_names": {
        "title": "リンクやアイコンボタンに操作名を付ける",
        "action": "アイコンだけのボタンや画像リンクに、aria-labelなどで「メニューを開く」「問い合わせへ進む」のような操作名を付けてください。",
        "target": "a / button",
        "reason": "検索エンジン、AI、支援技術がリンク先やボタンの目的を判断しやすくなります。",
        "verification": "ボタンやリンクのHTMLを確認し、表示テキスト、aria-label、title、画像altのいずれかで目的が分かるか確認します。",
    },
    "form_labels": {
        "title": "入力欄に項目名を付ける",
        "action": "メールアドレス、相談内容、検索欄などの入力欄にlabelまたはaria-labelを付けてください。",
        "target": "input / select / textarea",
        "reason": "ユーザーが何を入力すればよいか分かり、AIや支援技術にもフォームの目的が伝わります。",
        "verification": "入力欄をクリックし、画面上またはHTML上で項目名が確認できるか見ます。",
    },
    "h1": {
        "title": "ページの主題をh1で1つ示す",
        "action": "ページで一番伝えたい主題をh1にし、ロゴや装飾だけがh1になっていないか確認してください。",
        "target": "h1",
        "reason": "検索エンジン、AI、読み上げ機能がページ全体のテーマをつかみやすくなります。",
        "verification": "ページ内のh1が1つで、ページ内容を説明しているか確認します。",
    },
    "heading_hierarchy": {
        "title": "見出しの順番を整理する",
        "action": "h1の下にh2、h2の下にh3という順で見出しを並べ、見出しだけでページの流れが分かるようにしてください。",
        "target": "h1-h6",
        "reason": "検索エンジン、AI、支援技術がページ構造を読み取りやすくなります。",
        "verification": "見出し一覧を確認し、h2からh4へ飛ぶような順番になっていないか見ます。",
    },
    "landmarks": {
        "title": "ページの主要領域を分かるHTMLにする",
        "action": "header、nav、main、footerを使い、ヘッダー・メニュー・本文・フッターの境界をHTMLで示してください。",
        "target": "header / nav / main / footer",
        "reason": "検索エンジン、AI、支援技術が本文やナビゲーションの位置を判断しやすくなります。",
        "verification": "HTMLにheader、nav、main、footerがあり、本文がmain内に入っているか確認します。",
    },
    "html_lang": {
        "title": "ページの言語を指定する",
        "action": "html要素にlangを設定してください。日本語ページなら <html lang=\"ja\"> が目安です。",
        "target": "html lang",
        "reason": "検索エンジン、AI、読み上げ機能がページの言語を判別しやすくなります。",
        "verification": "HTML先頭のhtml要素にlang属性があるか確認します。",
    },
    "title": {
        "title": "ページ固有のtitleを入れる",
        "action": "ブラウザタブや検索結果に出るtitleに、ページ固有の内容を短く入れてください。",
        "target": "title",
        "reason": "検索結果、AIの要約、ブラウザタブでページ内容が伝わりやすくなります。",
        "verification": "ブラウザタブ名とHTMLのtitleを確認し、ページ内容と一致しているか見ます。",
    },
    "iframe_titles": {
        "title": "埋め込み枠に内容名を付ける",
        "action": "地図、動画、予約フォームなどのiframeに、内容が分かるtitleを入れてください。",
        "target": "iframe title",
        "reason": "支援技術が埋め込み内容を説明でき、AIにもページ内の役割が伝わりやすくなります。",
        "verification": "iframeのHTMLにtitleがあり、「アクセス地図」「紹介動画」など内容が分かるか確認します。",
    },
    "color_contrast": {
        "title": "文字色と背景色を読みやすくする",
        "action": "本文、ボタン、ナビゲーション、注記の文字色と背景色を見直し、薄すぎる組み合わせを避けてください。",
        "target": "文字色 / 背景色",
        "reason": "弱視の人、屋外や低品質ディスプレイで見る人が内容を読み取りやすくなり、離脱も減らしやすくなります。",
        "verification": "対象箇所を実ブラウザで確認し、通常文字は4.5:1以上を目安にコントラストを再確認します。",
    },
    "zoom_scaling": {
        "title": "スマホで拡大できる設定にする",
        "action": "meta viewport の user-scalable=no や maximum-scale=1 を外し、利用者が文字や画面を拡大できるようにしてください。",
        "target": "meta viewport",
        "reason": "小さい文字を拡大して読む人にとって、拡大できないページは閲覧の大きな阻害要因になります。",
        "verification": "スマホ表示でピンチズームできるか確認し、HTMLのviewport指定に拡大禁止が残っていないか見ます。",
    },
    "aria_semantics": {
        "title": "ARIAの役割と状態を正しく整理する",
        "action": "roleとaria属性の組み合わせを見直し、部品の意味や状態が支援技術へ誤って伝わらないようにしてください。",
        "target": "role / aria-*",
        "reason": "画面上は動いて見えても、読み上げ機能では操作名や状態が誤って伝わることがあります。",
        "verification": "該当要素のroleとaria属性を確認し、不要なARIAを削除するか正しいHTML要素へ置き換えます。",
    },
    "keyboard_focus": {
        "title": "キーボードで自然に操作できるようにする",
        "action": "Tabキーで主要なリンク、ボタン、入力欄へ順番に移動でき、フォーカス位置が見える状態にしてください。",
        "target": "Tab順序 / focus",
        "reason": "マウスを使わない人や一時的に細かい操作が難しい人でも、問い合わせや購入などの主要操作を完了しやすくなります。",
        "verification": "マウスを使わずTabとEnterだけで主要導線を操作し、順序とフォーカス表示を確認します。",
    },
    "screen_reader_structure": {
        "title": "読み上げで伝わるページ構造にする",
        "action": "見出し、ランドマーク、操作部品名を整理し、読み上げでもページの現在地と次の操作が分かる構造にしてください。",
        "target": "見出し / landmark / 操作部品",
        "reason": "検索エンジン、AI、読み上げ機能がページの意味と導線を理解しやすくなります。",
        "verification": "見出し一覧、ランドマーク一覧、操作部品名を確認し、名前なしや構造の飛びを直します。",
    },
}


def _first_issue_element(group: Dict[str, Any]) -> str:
    for issue in group.get("issues") or []:
        if not isinstance(issue, dict):
            continue
        element = _safe_text(issue.get("element"))
        if element:
            return element
    return _safe_text(group.get("label") or group.get("name") or group.get("id"))


def _first_issue_text(group: Dict[str, Any]) -> str:
    issues = group.get("issues") or []
    if not isinstance(issues, list):
        issues = [issues]
    for issue in issues:
        if isinstance(issue, dict):
            text = _safe_text(issue.get("issue") or issue.get("message") or issue.get("reason"))
        else:
            text = _safe_text(issue)
        if text:
            return text
    return ""


def _build_base_action(group: Dict[str, Any], template: Dict[str, str], rank: int, *, detection_source: str) -> Dict[str, Any]:
    group_id = _safe_text(group.get("id"))
    affected_count = _safe_int(group.get("affected_count"))
    audience = _AUDIENCE_COPY_BY_GROUP.get(group_id) or {
        "action": template["action"],
        "review_area": template["target"],
        "handoff_to": "Web制作担当",
        "impact": template["reason"],
        "confirmation": template["verification"],
    }
    target_element = _first_issue_element(group)
    source_label = "実ブラウザ自動検出" if detection_source == "browser" else "HTML自動検出"
    return {
        "priority_rank": rank,
        "priority_score": _priority_score(group),
        "title": template["title"],
        "action": template["action"],
        "target": template["target"],
        "target_element": target_element,
        "reason": template["reason"],
        "verification": template["verification"],
        "audience": {
            "action": audience["action"],
            "impact": audience["impact"],
            "review_area": audience["review_area"],
            "handoff_to": audience["handoff_to"],
            "confirmation": audience["confirmation"],
        },
        "engineer": {
            "target": template["target"],
            "target_element": target_element,
            "task": _ENGINEER_WORK_BY_GROUP.get(group_id, template["action"]),
            "verification": template["verification"],
            "detection_source": source_label,
            "raw_issue": _first_issue_text(group),
        },
        "affected_count": affected_count,
        "group": group_id,
        "category": "アクセシビリティ",
        "impact": _impact_from_group(group),
        "urgency": _STATUS_URGENCY.get(_safe_text(group.get("status")), "中"),
        "effort": _EFFORT_BY_GROUP.get(group_id, "中"),
        "status": _safe_text(group.get("status")),
    }


def _metadata(
    *,
    html_hash: str,
    model: str,
    reasoning_effort: str,
    max_parallel: int,
    llm_enabled: bool,
    llm_used: bool = False,
    fallback_used: bool = False,
    error: str = "",
) -> Dict[str, Any]:
    return {
        "ruleset_version": RULESET_VERSION,
        "prompt_version": PROMPT_VERSION,
        "html_hash": html_hash,
        "model": model,
        "reasoning": {"effort": reasoning_effort},
        "temperature": DEFAULT_TEMPERATURE,
        "llm_enabled": llm_enabled,
        "llm_used": llm_used,
        "fallback_used": fallback_used,
        "fallback_reason": error,
        "max_parallel": max_parallel,
    }


def _parse_llm_json_response(response: Any) -> Dict[str, Any]:
    text = _safe_text(getattr(response, "output_text", ""))
    if not text:
        output = getattr(response, "output", None) or []
        chunks: List[str] = []
        for item in output:
            for content in getattr(item, "content", []) or []:
                value = getattr(content, "text", None)
                if value:
                    chunks.append(str(value))
        text = "\n".join(chunks)
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("llm_response_not_object")
    return {
        key: _safe_text(parsed.get(key))
        for key in ("title", "action", "reason", "verification")
        if _safe_text(parsed.get(key))
    }


def _format_single_action_with_llm(
    client: Any,
    action: Dict[str, Any],
    *,
    model: str,
    reasoning_effort: str,
    html_hash: str,
) -> Dict[str, str]:
    safe_action = {
        key: sanitize_untrusted_prompt_text(action.get(key), max_chars=320)
        for key in ("title", "action", "target", "target_element", "reason", "verification", "group")
    }
    prompt = {
        "prompt_version": PROMPT_VERSION,
        "ruleset_version": RULESET_VERSION,
        "html_hash": html_hash,
        "instruction": (
            "日本語で、Web担当者が具体的に実行できる短い改善文に整えてください。"
            "順位、件数、重要度、対象groupは変更しないでください。"
        ),
        "action": safe_action,
    }
    data, _response = call_structured(
        client,
        model=model,
        reasoning_effort=reasoning_effort,
        input_messages=[
            {
                "role": "system",
                "content": "You rewrite accessibility action copy only. Return JSON matching the schema.",
            },
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        json_schema_name="accessibility_action_copy",
        json_schema=ACTION_COPY_SCHEMA,
        max_output_tokens=500,
        temperature=DEFAULT_TEMPERATURE,
    )
    return {
        key: _safe_text(data.get(key))
        for key in ("title", "action", "reason", "verification")
        if _safe_text(data.get(key))
    }


def _apply_llm_formatting(
    actions: List[Dict[str, Any]],
    *,
    client: Any,
    model: str,
    reasoning_effort: str,
    html_hash: str,
    max_parallel: int,
) -> tuple[List[Dict[str, Any]], bool, str]:
    if not actions:
        return actions, False, ""

    formatted_by_index: Dict[int, Dict[str, str]] = {}
    try:
        with ThreadPoolExecutor(max_workers=max(1, min(max_parallel, 5))) as executor:
            futures = {
                executor.submit(
                    _format_single_action_with_llm,
                    client,
                    action,
                    model=model,
                    reasoning_effort=reasoning_effort,
                    html_hash=html_hash,
                ): index
                for index, action in enumerate(actions)
            }
            for future in as_completed(futures):
                formatted_by_index[futures[future]] = future.result()
    except Exception as exc:
        return actions, False, str(exc)

    merged = [dict(action) for action in actions]
    for index, rewrite in formatted_by_index.items():
        for field in ("title", "action", "reason", "verification"):
            if rewrite.get(field):
                merged[index][field] = rewrite[field]
        merged[index]["copy_source"] = "llm"
    return merged, bool(formatted_by_index), ""


def build_accessibility_improvement_actions(
    site_health: Dict[str, Any],
    *,
    limit: int = 5,
    html: Optional[str] = None,
    use_llm: bool = False,
    llm_client: Any = None,
    model: Optional[str] = None,
    reasoning_effort: str = DEFAULT_REASONING_EFFORT,
    max_parallel: int = DEFAULT_MAX_PARALLEL,
) -> Dict[str, Any]:
    """Return score and concrete non-engineer action cards from accessibility raw data.

    LLM formatting is optional and fail-closed: failure returns the exact
    rule-based fallback count and order.
    """
    accessibility = (site_health or {}).get("accessibility") or {}
    raw = accessibility.get("raw") or {}
    formatted = accessibility.get("formatted") or {}
    if not isinstance(raw, dict):
        raw = {}
    score = _safe_int(raw.get("score") if isinstance(raw, dict) else None)
    if score <= 0:
        score = _safe_int(formatted.get("score") if isinstance(formatted, dict) else None)
    resolved_model = _safe_text(model) or DEFAULT_LLM_MODEL
    resolved_reasoning = _safe_text(reasoning_effort).lower() or "low"
    if resolved_reasoning not in _REASONING_EFFORTS:
        resolved_reasoning = "low"
    bounded_parallel = max(1, min(_safe_int(max_parallel) or DEFAULT_MAX_PARALLEL, 5))
    html_hash = _resolve_html_hash(site_health or {}, raw, html)

    issue_groups = raw.get("issue_groups")
    if not isinstance(issue_groups, list):
        issue_groups = []
    detection_source = _safe_text(raw.get("detection_source") or accessibility.get("source") or formatted.get("detection_source"))

    ranked_groups = sorted(
        [group for group in issue_groups if isinstance(group, dict)],
        key=_priority_sort_key,
    )

    actions: List[Dict[str, Any]] = []
    for group in ranked_groups:
        group_id = _safe_text(group.get("id"))
        template = ACTION_TEMPLATES.get(group_id)
        if not template:
            continue
        affected_count = _safe_int(group.get("affected_count"))
        if affected_count <= 0:
            continue
        actions.append(_build_base_action(group, template, len(actions) + 1, detection_source=detection_source))
        if len(actions) >= limit:
            break

    llm_enabled = bool(use_llm)
    llm_error = ""
    llm_used = False
    if llm_enabled and actions:
        client = llm_client
        api_key = resolve_env_var("OPENAI_API_KEY")
        if client is None and api_key:
            try:
                from openai import OpenAI

                client = OpenAI(api_key=api_key, timeout=config.OPENAI_TIMEOUT)
            except Exception as exc:
                llm_error = str(exc)
        if client is not None:
            actions, llm_used, llm_error = _apply_llm_formatting(
                actions,
                client=client,
                model=resolved_model,
                reasoning_effort=resolved_reasoning,
                html_hash=html_hash,
                max_parallel=bounded_parallel,
            )
        elif not llm_error:
            llm_error = "openai_client_unavailable"

    browser_source = detection_source == "browser"
    actual_issue_count = sum(
        _safe_int(group.get("affected_count"))
        for group in issue_groups
        if isinstance(group, dict)
    )
    confirmation_items = []
    if not actions:
        confirmation_items.append(
            {
                "title": "固定テンプレートの要対応カードはありません",
                "detail": "自動検出された具体的な改善候補が0件のため、汎用修正カードは前面表示しません。必要に応じて定期確認として扱います。",
                "detection_source": "実ブラウザ自動検出" if browser_source else "HTML自動検出",
            }
        )
    return {
        "score": score,
        "title": "見やすさ・使いやすさ改善",
        "summary": (
            "実ブラウザで見つけた、人が読みやすく操作しやすいサイトにするための作業です。"
            if browser_source
            else "検索エンジン・AI・読み上げ機能が読み取りやすいHTML構造に整えるための作業です。"
        ),
        "actions": actions[:limit],
        "actual_issue_count": actual_issue_count,
        "confirmation_items": confirmation_items,
        "metadata": _metadata(
            html_hash=html_hash,
            model=resolved_model,
            reasoning_effort=resolved_reasoning,
            max_parallel=bounded_parallel,
            llm_enabled=llm_enabled,
            llm_used=llm_used,
            fallback_used=llm_enabled and not llm_used,
            error=llm_error,
        ),
    }
