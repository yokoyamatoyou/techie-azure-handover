# -*- coding: utf-8 -*-
"""コンテンツとSchemaのギャップ分析モジュール (LLM使用)"""
import os
from typing import Dict, List, Any

from openai import OpenAI

from core.config import config


def analyze_content_schema_gap(
    content_text: str,
    schema_data: List[Dict[str, Any]],
    site_type: str = "company",
) -> Dict[str, Any]:
    """コンテンツとSchemaのギャップをLLMで分析"""
    if not content_text:
        return {
            "gaps": [],
            "recommendations": ["本文が空のため分析できませんでした"],
            "aio_improvement_potential": 0,
        }

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=config.OPENAI_TIMEOUT)

    prompt = f"""
以下のWebページ本文とSchema.org （JSON-LD）を比較し、
コンテンツで主張しているがSchemaに反映されていない情報を列挙してください。

## 本文（抜粋）
{content_text[:2000]}

## Schema.org データ
{schema_data}

## サイト種別
{site_type}

## 出力形式（JSON）
{{
    "gaps": [
        {{"content_claim": "本文に書かれている主張", "missing_in_schema": "対応するスキーマプロパティ名"}}
    ],
    "recommendations": ["推奨する改善アクション"],
    "aio_improvement_potential": 0-100の数値
}}
"""

    try:
        response = client.chat.completions.create(
            model=config.MODEL_DEFAULT,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=1000,
        )
        import json
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {
            "gaps": [],
            "recommendations": [f"分析エラー: {str(e)}"],
            "aio_improvement_potential": 0,
            "error": str(e),
        }


if __name__ == "__main__":
    test_content = "株式会社テストは創業50年の老舗企業です。ISO9001認証取得済み。"
    test_schema = [{"@type": "Organization", "name": "株式会社テスト"}]
    result = analyze_content_schema_gap(test_content, test_schema)
    print(f"Gaps: {result.get('gaps', [])}")
    print(f"Potential: {result.get('aio_improvement_potential', 0)}")
