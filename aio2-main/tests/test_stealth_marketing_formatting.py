from __future__ import annotations

from core.legal_checks.stealth_marketing import format_stealth_marketing_result


def test_format_stealth_marketing_explains_non_affiliate_score_impact() -> None:
    formatted = format_stealth_marketing_result(
        {
            "compliance_status": "ok",
            "affiliate_detection": {
                "is_affiliate": False,
                "confidence": 0.2,
                "indicators": [],
                "affiliate_links_count": 0,
                "content_pattern_count": 2,
            },
            "disclosure_check": {"has_disclosure": False},
            "issues": [],
            "recommendations": [],
        }
    )

    item = formatted["items"][0]

    assert "広告・PR要素に表記不足がないか" in formatted["summary"]
    assert item["text"] == "PR表記が必要なアフィリエイト要素: 未検出"
    assert "既知のASPリンクやアフィリエイトURLは未検出" in item["subtext"]
    assert "スコア低下/要対応になるのは、広告・PR要素があるのに表記が不足する場合" in item["subtext"]


def test_format_stealth_marketing_explains_pr_disclosure_missing_risk() -> None:
    formatted = format_stealth_marketing_result(
        {
            "compliance_status": "violation",
            "affiliate_detection": {
                "is_affiliate": True,
                "confidence": 0.8,
                "indicators": ["アフィリエイトリンク 9件検出"],
                "affiliate_links_count": 9,
                "content_pattern_count": 3,
            },
            "disclosure_check": {"has_disclosure": False},
            "issues": [
                {
                    "severity": "high",
                    "issue": "アフィリエイトコンテンツにPR表記がありません",
                    "detail": "アフィリエイトリンク 9件が検出されましたが、広告表記が見つかりません",
                }
            ],
            "recommendations": ["記事冒頭に「【PR】」または「広告」の表記を追加してください"],
        }
    )

    assert formatted["items"][0]["text"] == "PR表記確認が必要なアフィリエイト要素: 検出（信頼度 80%）"
    assert "PR/広告表記の有無と見やすさを確認" in formatted["items"][0]["subtext"]
    assert formatted["items"][1]["text"] == "PR表記: 未検出"
    assert "広告であることが分かるPR/広告表記" in formatted["items"][1]["subtext"]
