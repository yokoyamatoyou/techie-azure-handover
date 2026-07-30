"""Detail writing profile option label constants."""

from __future__ import annotations

from typing import Dict


BRANDING_SUBTYPE_LABELS: Dict[str, str] = {
    "company": "会社紹介を中心にする",
    "product": "製品紹介を中心にする",
    "service": "サービス紹介を中心にする",
}

BRANDING_FOCUS_LABELS: Dict[str, str] = {
    "awareness_build": "まず知ってもらう",
    "difference_proof": "違いを伝える",
    "choice_criteria": "選ぶ基準を作る",
    "category_creation": "新しい見方を作る",
}

TONE_PROFILE_LABELS: Dict[str, str] = {
    "auto": "記事に合わせて自然に書く",
    "calm": "落ち着いて解説する",
    "warm": "やさしく寄り添う",
    "passionate": "熱意をもって伝える",
    "formal": "端正にまとめる",
}

CONTENT_GOAL_LABELS: Dict[str, str] = {
    "auto": "自動（おすすめ）",
    "interest": "興味を惹く（読了率重視）",
    "explain": "説明したい（理解重視）",
    "action": "行動を促したい（CTA重視）",
    "trust": "信頼を高めたい（根拠重視）",
}

WRITING_FOCUS_LABELS: Dict[str, str] = {
    "auto": "自動（おすすめ）",
    "explanation": "解説メイン（わかりやすさ重視）",
    "experience": "経験メイン（体験・感情重視）",
    "analysis": "分析メイン（根拠・比較重視）",
}

LENGTH_MODE_LABELS: Dict[str, str] = {
    "adaptive": "自動（ソースに合わせる）",
    "short": "短め（お知らせ向け）",
    "normal": "普通（固定）",
    "long": "長め（深掘り）",
}

SELF_REFERENCE_POLICY_LABELS: Dict[str, str] = {
    "auto": "自動（おすすめ）",
    "watashi": "私",
    "watashitachi": "私たち",
    "tousha": "当社",
    "heisha": "弊社",
    "minimal": "一人称をなるべく使わない",
}

PATTERN_SELECT_LABELS: Dict[str, str] = {
    "auto": "自動（自由入力を優先）",
    "difference_first": "違いから入る",
    "scene_first": "場面から入る",
    "criteria_first": "判断軸から入る",
    "story_then_point": "体験から要点へ",
}
