"""
ベストプラクティス比較ロジック
"""

from typing import Dict, List


COMPLIANCE_DICTIONARY = {
    "return_policy": {
        "required": ["返品", "交換", "期間"],
        "forbidden": ["いかなる理由でも返品不可"],
    }
}


def check_best_practices(text: str) -> List[Dict]:
    """辞書ベースでガイドライン違反の表現を検出"""
    issues: List[Dict] = []
    if not text:
        return issues

    for key, rules in COMPLIANCE_DICTIONARY.items():
        required = rules.get("required", [])
        forbidden = rules.get("forbidden", [])

        missing = [term for term in required if term not in text]
        if missing:
            issues.append(
                {
                    "type": f"{key}_missing",
                    "severity": "warning",
                    "title": "必須表現の不足",
                    "detail": f"不足: {', '.join(missing)}",
                }
            )

        for phrase in forbidden:
            if phrase in text:
                issues.append(
                    {
                        "type": f"{key}_forbidden",
                        "severity": "warning",
                        "title": "不適切な表現",
                        "detail": f"検出: {phrase}",
                    }
                )

    return issues
