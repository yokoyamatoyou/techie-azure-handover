# -*- coding: utf-8 -*-
"""構造化データFAQ"""

from typing import Dict, List


SCHEMA_FAQ = [
    {
        "question": "構造化データは必須ですか？",
        "answer": "必須ではありませんが、設定することで検索結果での表示が改善される可能性があります。"
    },
    {
        "question": "JSON-LDとMicrodataのどちらを使うべきですか？",
        "answer": "GoogleはJSON-LDを推奨しています。実装が簡単で保守しやすいのが理由です。"
    },
    {
        "question": "構造化データを入れると順位が上がりますか？",
        "answer": "直接的に順位が上がるわけではありませんが、リッチリザルトでの表示改善が期待できます。"
    }
]


def get_schema_faq(schema_type: str = None) -> List[Dict]:
    """構造化データに関するFAQを返す"""
    return SCHEMA_FAQ
