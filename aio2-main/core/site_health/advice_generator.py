"""
パーソナライズドアドバイス生成エンジン
"""

from typing import Dict, List


class HealthAdviceGenerator:
    """サイトヘルスアドバイスを生成するクラス"""

    PRIORITY_ORDER = {
        "critical": 1,
        "high": 2,
        "medium": 3,
        "low": 4,
    }

    def generate_personalized_advice(self, site_health: Dict, industry: str, scores: Dict) -> List[Dict]:
        """
        パーソナライズドアドバイスを生成

        Args:
            site_health: サイトヘルス情報
            industry: 業種
            scores: 各項目のスコア

        Returns:
            優先度順のアドバイスリスト
        """
        advice = []

        if industry in ["healthcare", "finance"]:
            if not site_health.get("security", {}).get("has_csp"):
                advice.append(
                    {
                        "category": "セキュリティ強化",
                        "priority": "critical",
                        "why": f"{industry}業界では個人情報保護が法的に重要です",
                        "action": "CSPヘッダーを設定してください",
                        "expected_impact": "セキュリティリスクが大幅に低減します",
                    }
                )

        if scores.get("ogp", 100) < 80:
            advice.append(
                {
                    "category": "SNSシェア設定の改善",
                    "priority": "high" if industry in ["retail", "service"] else "medium",
                    "why": "SNS経由の流入を増やすために重要です",
                    "action": "OGP画像とdescriptionを設定してください",
                    "expected_impact": "SNSでのクリック率が30%向上する可能性があります",
                }
            )

        if not site_health.get("structured_data", {}).get("has_organization"):
            advice.append(
                {
                    "category": "構造化データの追加",
                    "priority": "high",
                    "why": "Googleの検索結果でリッチスニペットが表示されます",
                    "action": "Organization schemaを追加してください",
                    "expected_impact": "検索結果でのクリック率が15-20%向上します",
                }
            )

        if scores.get("accessibility", 100) < 70:
            advice.append(
                {
                    "category": "アクセシビリティ改善",
                    "priority": "medium",
                    "why": "すべてのユーザーがサイトを利用できるようにするため",
                    "action": "alt属性とARIAラベルを追加してください",
                    "expected_impact": "ユーザー体験が向上し、SEOにも好影響があります",
                }
            )

        advice.sort(key=lambda x: self.PRIORITY_ORDER[x["priority"]])

        return advice[:5]
