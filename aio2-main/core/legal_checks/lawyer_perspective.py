"""
弁護士視点の解説付与
"""

from typing import Dict, List


# 警告タイプごとの詳細情報
ISSUE_DETAILS = {
    "small_font": {
        "lawyer_comment": "文字が小さすぎると「認識できなかった」と主張されるリスクがあります。",
        "legal_basis": "消費者契約法第4条（重要事項の不実告知）",
        "what_is_checked": "規約・返品ポリシー等の重要情報のフォントサイズ",
        "best_practice": "重要情報は12px以上、できれば14px以上で表示",
        "bad_example": "font-size: 8px; で返品条件を記載",
        "good_example": "font-size: 14px; で返品条件を明確に表示",
        "how_to_fix": "CSSでfont-sizeを12px以上に変更してください",
    },
    "small_font_legal": {
        "lawyer_comment": "法的に重要な情報の文字が小さすぎると、説明義務違反と判断されるリスクがあります。",
        "legal_basis": "消費者契約法第4条、景品表示法第5条",
        "what_is_checked": "特商法表記、返品ポリシー、利用規約のフォントサイズ",
        "best_practice": "法的重要情報は本文と同等以上のサイズ（14px以上推奨）",
        "bad_example": "※返品は到着後3日以内（font-size: 8px）",
        "good_example": "返品について：到着後7日以内にご連絡ください（font-size: 14px）",
        "how_to_fix": "重要な規約・ポリシーは本文と同サイズ以上で表示してください",
    },
    "hidden_text": {
        "lawyer_comment": "重要事項が非表示だと不当表示とみなされる恐れがあります。",
        "legal_basis": "景品表示法第5条（優良誤認・有利誤認）",
        "what_is_checked": "display:none や visibility:hidden で隠された重要テキスト",
        "best_practice": "重要情報は常に表示状態にする",
        "bad_example": "<p style='display:none'>※別途送料がかかります</p>",
        "good_example": "<p>※別途送料がかかります（地域により異なります）</p>",
        "how_to_fix": "display:none を削除し、テキストを表示状態にしてください",
    },
    "low_reachability": {
        "lawyer_comment": "リンクが見つけにくい場合、説明義務を果たしていないと判断される可能性があります。",
        "legal_basis": "特定商取引法第11条（通信販売の表示義務）",
        "what_is_checked": "リンクテキストの長さ、画像のみのリンク、アイコンのみのリンク",
        "best_practice": "リンク先の内容が分かる具体的なテキストを使用（5文字以上推奨）",
        "bad_example": "<a href='/policy'>こちら</a>",
        "good_example": "<a href='/policy'>返品・交換ポリシーの詳細</a>",
        "how_to_fix": "「こちら」「詳細」ではなく、リンク先の内容が分かる文言に変更してください",
    },
    "return_policy_missing": {
        "lawyer_comment": "返品・交換の条件が不明確だとトラブル時の紛争リスクが高まります。",
        "legal_basis": "特定商取引法第11条第1項第4号",
        "what_is_checked": "返品ポリシーに「返品」「交換」「期間」の記載があるか",
        "best_practice": "返品条件、交換条件、申請期間を明記",
        "bad_example": "返品はお受けしております。",
        "good_example": "返品：商品到着後7日以内にご連絡ください。交換：同一商品との交換が可能です。",
        "how_to_fix": "返品・交換の条件と期間を具体的に記載してください",
    },
    "return_policy_forbidden": {
        "lawyer_comment": "一律の返品不可は消費者契約法上、無効と判断されるケースがあります。",
        "legal_basis": "消費者契約法第8条〜10条（不当条項の無効）",
        "what_is_checked": "「いかなる理由でも返品不可」等の一律拒否表現",
        "best_practice": "正当な理由（開封済み、使用済み等）を条件とした返品制限",
        "bad_example": "いかなる理由でも返品・返金はお受けできません。",
        "good_example": "未開封・未使用の場合、7日以内に限り返品を承ります。",
        "how_to_fix": "一律拒否ではなく、条件付きの返品ポリシーに変更してください",
    },
}

# 後方互換性のため旧形式も維持
LAWYER_COMMENTS = {key: val["lawyer_comment"] for key, val in ISSUE_DETAILS.items()}


def attach_lawyer_comments(issues: List[Dict]) -> List[Dict]:
    """リスク項目に弁護士視点の解説を付与"""
    enriched = []
    for issue in issues:
        issue_type = issue.get("type", "")
        details = ISSUE_DETAILS.get(issue_type, {})

        enriched_issue = {
            **issue,
            "lawyer_comment": details.get("lawyer_comment", "詳細条件により法的評価が変わるため注意が必要です。"),
            "legal_basis": details.get("legal_basis", ""),
            "what_is_checked": details.get("what_is_checked", ""),
            "best_practice": details.get("best_practice", ""),
            "bad_example": details.get("bad_example", ""),
            "good_example": details.get("good_example", ""),
            "how_to_fix": details.get("how_to_fix", ""),
        }
        enriched.append(enriched_issue)
    return enriched


def get_issue_details(issue_type: str) -> Dict:
    """特定の警告タイプの詳細情報を取得"""
    return ISSUE_DETAILS.get(issue_type, {})


# サイト種別ごとの関連警告タイプ
SITE_TYPE_RELEVANT_ISSUES = {
    "EC": {
        "small_font", "small_font_legal", "hidden_text", "low_reachability",
        "return_policy_missing", "return_policy_forbidden",
    },
    "企業（EC機能あり）": {
        "small_font", "small_font_legal", "hidden_text", "low_reachability",
        "return_policy_missing", "return_policy_forbidden",
    },
    "企業": {
        "small_font", "hidden_text",  # 返品ポリシーは不要
    },
    "メディア": {
        "small_font", "hidden_text",
    },
    "ブログ": {
        "small_font",
    },
}


def filter_issues_by_site_type(issues: List[Dict], site_type: str, is_ec: bool) -> List[Dict]:
    """サイト種別に応じて関連する警告のみをフィルタリング"""
    if is_ec:
        # ECサイトは全ての警告を表示
        return issues

    relevant_types = SITE_TYPE_RELEVANT_ISSUES.get(site_type, {"small_font", "hidden_text"})

    filtered = []
    for issue in issues:
        issue_type = issue.get("type", "")
        # 関連する警告タイプのみを含める
        if issue_type in relevant_types:
            filtered.append(issue)
        # 関連しない警告は完全に除外（参考情報としても表示しない）

    return filtered
