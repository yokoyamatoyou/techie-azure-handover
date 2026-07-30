# -*- coding: utf-8 -*-
"""機械可読アクセシビリティ改善スコア."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup, Tag


SCORING_VERSION = "accessibility-machine-readable-v1"

ACCESSIBILITY_SCORE_WEIGHTS: Dict[str, int] = {
    "html_lang": 8,
    "title": 8,
    "h1": 12,
    "heading_hierarchy": 12,
    "landmarks": 16,
    "image_alt": 14,
    "interactive_names": 12,
    "form_labels": 12,
    "iframe_titles": 6,
}

# Backward-compatible export name. The current scorer does not perform a
# certification-style判定; these are deterministic scoring groups only.
WCAG_CRITERIA = {
    key: {"name": key, "weight": weight}
    for key, weight in ACCESSIBILITY_SCORE_WEIGHTS.items()
}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _short_element(element: Tag, attrs: Tuple[str, ...] = ("id", "class", "href", "src", "name", "type")) -> str:
    parts = [element.name]
    for attr in attrs:
        if not element.has_attr(attr):
            continue
        raw = element.get(attr)
        if isinstance(raw, list):
            raw = " ".join(str(item) for item in raw[:3])
        value = _clean_text(raw)
        if value:
            parts.append(f'{attr}="{value[:60]}"')
    return "<" + " ".join(parts) + ">"


def _issue(element: Optional[Tag], issue: str, suggestion: str) -> Dict[str, str]:
    payload = {
        "issue": issue,
        "suggestion": suggestion,
    }
    if element is not None:
        payload["element"] = _short_element(element)
    return payload


def _unique_elements_by_signature(elements: List[Tag]) -> List[Tag]:
    unique: List[Tag] = []
    seen: set[str] = set()
    for element in elements:
        signature = _short_element(element, attrs=("id", "class", "href", "src", "name", "type"))
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(element)
    return unique


class AccessibilityChecker:
    """HTMLから自動検出できるアクセシビリティ改善余地を採点する."""

    def __init__(self, html: str):
        self.html = html or ""
        self.soup = BeautifulSoup(self.html, "html.parser")

    def _text_by_idrefs(self, idrefs: str) -> str:
        texts: List[str] = []
        for ref in idrefs.split():
            target = self.soup.find(id=ref)
            if target:
                text = _clean_text(target.get_text(" ", strip=True))
                if text:
                    texts.append(text)
        return " ".join(texts)

    def _accessible_name_candidate(self, element: Tag) -> str:
        aria_label = _clean_text(element.get("aria-label"))
        if aria_label:
            return aria_label

        labelledby = _clean_text(element.get("aria-labelledby"))
        if labelledby:
            text = self._text_by_idrefs(labelledby)
            if text:
                return text

        text = _clean_text(element.get_text(" ", strip=True))
        if text:
            return text

        title = _clean_text(element.get("title"))
        if title:
            return title

        for img in element.find_all("img"):
            alt = _clean_text(img.get("alt"))
            if alt:
                return alt

        return ""

    def _has_form_label(self, control: Tag) -> bool:
        control_id = _clean_text(control.get("id"))
        if control_id and self.soup.find("label", attrs={"for": control_id}):
            return True

        if control.find_parent("label"):
            return True

        if _clean_text(control.get("aria-label")):
            return True

        labelledby = _clean_text(control.get("aria-labelledby"))
        if labelledby and self._text_by_idrefs(labelledby):
            return True

        if _clean_text(control.get("title")):
            return True

        return False

    def _visible_text_length(self) -> int:
        soup = BeautifulSoup(self.html, "html.parser")
        for hidden in soup(["script", "style", "noscript", "template"]):
            hidden.decompose()
        text = _clean_text(soup.get_text(" ", strip=True))
        return len(text)

    def _structure_count(self) -> int:
        structure_tags = (
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "main",
            "nav",
            "header",
            "footer",
            "img",
            "a",
            "button",
            "input",
            "select",
            "textarea",
            "iframe",
            "p",
            "li",
            "section",
            "article",
        )
        return len(self.soup.find_all(structure_tags))

    def _score_cap(self, score: float) -> Tuple[float, Dict[str, Any]]:
        text_length = self._visible_text_length()
        structure_count = self._structure_count()

        cap = 100
        reason = ""
        if text_length < 20 and structure_count < 5:
            cap = 35
            reason = "本文量とHTML構造量が少ないため、自動検出の上限を35点に制限"
        elif text_length < 80 and structure_count < 8:
            cap = 60
            reason = "本文量またはHTML構造量が少ないため、自動検出の上限を60点に制限"
        elif text_length < 200 and structure_count < 12:
            cap = 80
            reason = "検出できる構造が限定的なため、自動検出の上限を80点に制限"

        capped_score = min(score, cap)
        return capped_score, {
            "cap": cap,
            "applied": capped_score < score,
            "reason": reason,
            "text_length": text_length,
            "structure_count": structure_count,
        }

    def _group(
        self,
        group_id: str,
        label: str,
        weight: int,
        ratio: float,
        total_count: int,
        affected_count: int,
        issues: List[Dict[str, str]],
        action: str,
    ) -> Dict[str, Any]:
        normalized_ratio = max(0.0, min(1.0, ratio))
        group_score = round(weight * normalized_ratio, 2)
        if affected_count == 0:
            status = "ok"
        elif normalized_ratio >= 0.7:
            status = "warning"
        else:
            status = "needs_work"

        return {
            "id": group_id,
            "name": label,
            "label": label,
            "weight": weight,
            "score": group_score,
            "ratio": round(normalized_ratio, 4),
            "status": status,
            "total_count": total_count,
            "affected_count": affected_count,
            "issues": issues[:10],
            "action": action,
        }

    def check_html_lang(self) -> Dict[str, Any]:
        html_tag = self.soup.find("html")
        has_lang = bool(html_tag and _clean_text(html_tag.get("lang")))
        issues = []
        if not has_lang:
            issues.append(_issue(html_tag, "html要素のlang属性が自動検出できません", '<html lang="ja"> のようにページ言語を指定してください'))
        return self._group(
            "html_lang",
            "html lang",
            ACCESSIBILITY_SCORE_WEIGHTS["html_lang"],
            1.0 if has_lang else 0.0,
            1,
            0 if has_lang else 1,
            issues,
            "html要素にページ言語を設定",
        )

    def check_title(self) -> Dict[str, Any]:
        title = self.soup.find("title")
        has_title = bool(title and _clean_text(title.get_text(" ", strip=True)))
        issues = []
        if not has_title:
            issues.append(_issue(title, "title要素のテキストが自動検出できません", "ページ内容を表すtitle要素をhead内に追加してください"))
        return self._group(
            "title",
            "title",
            ACCESSIBILITY_SCORE_WEIGHTS["title"],
            1.0 if has_title else 0.0,
            1,
            0 if has_title else 1,
            issues,
            "head内のtitleをページ固有の文言に設定",
        )

    def check_h1(self) -> Dict[str, Any]:
        h1s = self.soup.find_all("h1")
        empty_h1s = [h1 for h1 in h1s if not _clean_text(h1.get_text(" ", strip=True))]
        issues: List[Dict[str, str]] = []
        if not h1s:
            issues.append(_issue(None, "h1が自動検出できません", "ページの主題を表すh1を1つ追加してください"))
        if len(h1s) > 1:
            issues.append(_issue(h1s[1], f"h1が{len(h1s)}個あります", "主題のh1を1つに絞り、下位見出しはh2以降へ整理してください"))
        for h1 in empty_h1s[:5]:
            issues.append(_issue(h1, "空のh1があります", "h1にページ主題のテキストを入れてください"))

        if len(h1s) == 1 and not empty_h1s:
            ratio = 1.0
        elif h1s and not empty_h1s:
            ratio = 0.6
        elif h1s:
            ratio = 0.4
        else:
            ratio = 0.0

        return self._group(
            "h1",
            "h1",
            ACCESSIBILITY_SCORE_WEIGHTS["h1"],
            ratio,
            max(1, len(h1s)),
            len(issues),
            issues,
            "ページ主題を表すh1を1つに整理",
        )

    def check_heading_hierarchy(self) -> Dict[str, Any]:
        headings: List[Dict[str, Any]] = []
        for heading in self.soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            level = int(heading.name[1])
            headings.append({
                "level": level,
                "text": _clean_text(heading.get_text(" ", strip=True))[:80],
                "element": heading,
            })

        issues: List[Dict[str, str]] = []
        skip_count = 0
        empty_count = 0
        previous_level = 0
        for heading in headings:
            level = heading["level"]
            element = heading["element"]
            if not heading["text"]:
                empty_count += 1
                issues.append(_issue(element, f"h{level}が空です", "見出しにはセクション内容を表すテキストを入れてください"))
            if previous_level and level > previous_level + 1:
                skip_count += 1
                issues.append(_issue(element, f"h{previous_level}の後にh{level}があり、見出しレベルが飛んでいます", f"h{previous_level + 1}を挟むか、見出しレベルを調整してください"))
            previous_level = level

        if not headings:
            issues.append(_issue(None, "見出しが自動検出できません", "主要セクションをh2以降で構造化してください"))

        problem_count = skip_count + empty_count + (1 if not headings else 0)
        ratio = 1.0 if headings else 0.0
        if headings:
            ratio = max(0.0, 1.0 - (problem_count / max(1, len(headings))))

        group = self._group(
            "heading_hierarchy",
            "見出し階層",
            ACCESSIBILITY_SCORE_WEIGHTS["heading_hierarchy"],
            ratio,
            len(headings),
            problem_count,
            issues,
            "見出しをh1から順に階層化",
        )
        group["headings"] = [
            {"level": item["level"], "text": item["text"]}
            for item in headings[:20]
        ]
        return group

    def check_landmarks(self) -> Dict[str, Any]:
        landmark_queries = {
            "main": lambda: self.soup.find("main") or self.soup.find(attrs={"role": "main"}),
            "nav": lambda: self.soup.find("nav") or self.soup.find(attrs={"role": "navigation"}),
            "header": lambda: self.soup.find("header") or self.soup.find(attrs={"role": "banner"}),
            "footer": lambda: self.soup.find("footer") or self.soup.find(attrs={"role": "contentinfo"}),
        }
        missing = [name for name, finder in landmark_queries.items() if not finder()]
        issues = [
            _issue(None, f"{name} landmarkが自動検出できません", f"<{name}> または対応するroleで主要領域を示してください")
            for name in missing
        ]
        found_count = len(landmark_queries) - len(missing)
        return self._group(
            "landmarks",
            "main/nav/header/footer landmark",
            ACCESSIBILITY_SCORE_WEIGHTS["landmarks"],
            found_count / len(landmark_queries),
            len(landmark_queries),
            len(missing),
            issues,
            "main/nav/header/footerのランドマークを明示",
        )

    def check_images_alt(self) -> Dict[str, Any]:
        images = self.soup.find_all("img")
        missing = [img for img in images if img.get("alt") is None]
        issues = [
            _issue(img, "imgのalt属性が自動検出できません", '内容画像は説明的なalt、装飾画像は alt="" を設定してください')
            for img in missing[:10]
        ]
        with_alt = len(images) - len(missing)
        ratio = 1.0 if not images else with_alt / len(images)
        group = self._group(
            "image_alt",
            "img alt",
            ACCESSIBILITY_SCORE_WEIGHTS["image_alt"],
            ratio,
            len(images),
            len(missing),
            issues,
            "imgにalt属性を設定",
        )
        group.update({
            "total_images": len(images),
            "with_alt": len([img for img in images if img.get("alt") not in (None, "")]),
            "without_alt": len(missing),
            "decorative": len([img for img in images if img.get("alt") == ""]),
        })
        return group

    def check_interactive_names(self) -> Dict[str, Any]:
        controls = self.soup.find_all(["a", "button"])
        missing = _unique_elements_by_signature([
            control for control in controls if not self._accessible_name_candidate(control)
        ])
        issues = [
            _issue(control, f"{control.name}のaccessible name候補が自動検出できません", "テキスト、aria-label、aria-labelledby、title、画像altのいずれかで操作名を示してください")
            for control in missing[:10]
        ]
        ratio = 1.0 if not controls else max(0.0, 1.0 - (len(missing) / len(controls)))
        return self._group(
            "interactive_names",
            "a/button accessible name候補",
            ACCESSIBILITY_SCORE_WEIGHTS["interactive_names"],
            ratio,
            len(controls),
            len(missing),
            issues,
            "リンクとボタンの操作名を自動検出できる形にする",
        )

    def check_form_labels(self) -> Dict[str, Any]:
        skip_types = {"hidden", "submit", "button", "reset", "image"}
        controls = [
            control
            for control in self.soup.find_all(["input", "select", "textarea"])
            if control.name != "input" or _clean_text(control.get("type") or "text").lower() not in skip_types
        ]
        missing = [control for control in controls if not self._has_form_label(control)]
        issues = [
            _issue(control, f"{control.name}のlabel候補が自動検出できません", "label要素、aria-label、aria-labelledby、titleのいずれかで入力目的を示してください")
            for control in missing[:10]
        ]
        labelled = len(controls) - len(missing)
        ratio = 1.0 if not controls else labelled / len(controls)
        return self._group(
            "form_labels",
            "input/select/textarea label",
            ACCESSIBILITY_SCORE_WEIGHTS["form_labels"],
            ratio,
            len(controls),
            len(missing),
            issues,
            "フォーム部品にlabelを設定",
        )

    def check_iframe_titles(self) -> Dict[str, Any]:
        iframes = self.soup.find_all("iframe")
        missing = [iframe for iframe in iframes if not _clean_text(iframe.get("title"))]
        issues = [
            _issue(iframe, "iframeのtitleが自動検出できません", "埋め込み内容を説明するtitle属性を設定してください")
            for iframe in missing[:10]
        ]
        titled = len(iframes) - len(missing)
        ratio = 1.0 if not iframes else titled / len(iframes)
        return self._group(
            "iframe_titles",
            "iframe title",
            ACCESSIBILITY_SCORE_WEIGHTS["iframe_titles"],
            ratio,
            len(iframes),
            len(missing),
            issues,
            "iframeに内容を表すtitleを設定",
        )

    def run_all_checks(self) -> Dict[str, Any]:
        """全チェックを実行し、deterministicな改善スコアを返す."""
        groups = [
            self.check_html_lang(),
            self.check_title(),
            self.check_h1(),
            self.check_heading_hierarchy(),
            self.check_landmarks(),
            self.check_images_alt(),
            self.check_interactive_names(),
            self.check_form_labels(),
            self.check_iframe_titles(),
        ]
        raw_score = round(sum(group["score"] for group in groups), 2)
        capped_score, cap_info = self._score_cap(raw_score)
        score = round(capped_score, 0)
        score_status = _score_status(score)

        issue_groups = [group for group in groups if group["affected_count"] > 0]
        affected_counts = {
            group["id"]: group["affected_count"]
            for group in groups
        }
        affected_counts.update({
            "total_issues": sum(group["affected_count"] for group in groups),
            "text_length": cap_info["text_length"],
            "structure_count": cap_info["structure_count"],
            "score_cap": cap_info["cap"],
        })

        top_actions = [
            {
                "group": group["id"],
                "label": group["label"],
                "action": group["action"],
                "affected_count": group["affected_count"],
                "weight": group["weight"],
            }
            for group in sorted(issue_groups, key=lambda item: (item["weight"], item["affected_count"]), reverse=True)[:5]
        ]
        if cap_info["applied"]:
            top_actions.insert(0, {
                "group": "content_structure_volume",
                "label": "本文量/構造量",
                "action": "本文とHTML構造を増やして自動検出できる範囲を広げる",
                "affected_count": 1,
                "weight": 0,
            })

        return {
            "score": int(score),
            "raw_score": raw_score,
            "score_status": score_status,
            "issue_groups": issue_groups,
            "affected_counts": affected_counts,
            "top_actions": top_actions[:5],
            "scoring_version": SCORING_VERSION,
            "score_cap": cap_info,
            "checks": {group["id"]: group for group in groups},
        }


def _score_status(score: float) -> str:
    if score >= 80:
        return "good"
    if score >= 50:
        return "needs_attention"
    return "needs_work"


def get_wcag_compliance_level(results: Dict[str, Any]) -> Dict[str, Any]:
    """互換API: 現在は自動検出の改善スコア概要を返す."""
    return {
        "label": "見やすさ・使いやすさ改善スコア",
        "method": "自動検出",
        "score": int(results.get("score", 0) or 0),
        "score_status": results.get("score_status", "needs_work"),
        "scoring_version": results.get("scoring_version", SCORING_VERSION),
    }


def format_accessibility_result(result: Dict[str, Any], mode: str = "simple") -> Dict[str, Any]:
    """UI向けに改善スコア結果を整形する."""
    score = int(result.get("score", 0) or 0)
    score_status = result.get("score_status") or _score_status(score)

    if score_status == "good":
        status = "改善スコア: 良好"
        status_color = "success"
    elif score_status == "needs_attention":
        status = "改善スコア: 改善推奨"
        status_color = "warning"
    else:
        status = "改善スコア: 要改善"
        status_color = "danger"

    items: List[Dict[str, Any]] = []
    for group in (result.get("checks") or {}).values():
        issues = group.get("issues", [])
        if group.get("affected_count", 0) == 0:
            icon = "自動検出"
            text = f"{group.get('label', group.get('name', '項目'))}: 自動検出で改善点なし"
            subtext = ""
        else:
            icon = "改善候補"
            text = f"{group.get('label', group.get('name', '項目'))}: {group.get('affected_count', len(issues))}件の改善候補"
            subtext = issues[0].get("issue", "") if issues else group.get("action", "")

        items.append({
            "icon": icon,
            "text": text,
            "subtext": subtext,
            "group": group.get("id", ""),
        })

    cap_info = result.get("score_cap") or {}
    recommendations = [
        {"recommendation": action.get("action", ""), "category": action.get("label", "")}
        for action in result.get("top_actions", [])
    ]
    if cap_info.get("applied") and cap_info.get("reason"):
        recommendations.insert(0, {"recommendation": cap_info["reason"], "category": "自動検出"})

    faq = [
        {
            "question": "この改善スコアは何を見ていますか？",
            "answer": "HTMLから自動検出できる言語指定、title、見出し、ランドマーク、alt、操作名、フォームラベル、iframe titleだけを採点します。",
        },
        {
            "question": "点数が高ければ十分ですか？",
            "answer": "いいえ。自動検出できないキーボード操作、読み上げ順、視覚的な分かりやすさなどは別途確認が必要です。",
        },
    ]

    return {
        "title": "見やすさ・使いやすさ改善スコア",
        "subtitle": "自動検出できるHTML構造だけを採点",
        "status": status,
        "status_color": status_color,
        "score": score,
        "score_status": score_status,
        "scoring_version": result.get("scoring_version", SCORING_VERSION),
        "items": items,
        "recommendations": recommendations,
        "faq": faq if mode == "simple" else [],
    }


ACCESSIBILITY_IMPROVEMENTS = {
    "missing_alt": {
        "simple": "画像にalt属性を追加してください",
        "detail": "自動検出ではalt属性の有無だけを確認します。内容画像は説明的なalt、装飾画像は空のaltを設定してください。",
        "example": '<img src="product.jpg" alt="青いTシャツ、Mサイズ、綿100%">',
    },
    "heading_skip": {
        "simple": "見出しの順番を整理してください",
        "detail": "見出しレベルが飛ぶと、ページ構造を機械的に把握しにくくなります。h1、h2、h3の順に整理してください。",
        "example": "<h1>ページタイトル</h1><h2>セクション</h2><h3>サブセクション</h3>",
    },
    "missing_name": {
        "simple": "リンクやボタンの操作名を追加してください",
        "detail": "テキスト、aria-label、aria-labelledby、title、画像altのいずれかで操作内容を自動検出できるようにしてください。",
        "example": '<button aria-label="メニューを開く">...</button>',
    },
    "missing_label": {
        "simple": "フォーム入力欄にlabelを追加してください",
        "detail": "label要素、aria-label、aria-labelledby、titleのいずれかで入力目的を自動検出できるようにしてください。",
        "example": '<label for="email">メールアドレス</label><input type="email" id="email">',
    },
}
