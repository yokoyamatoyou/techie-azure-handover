# -*- coding: utf-8 -*-
"""構造化データ提案エンジン"""

from typing import Dict, List


class SchemaSuggester:
    """業種・コンテンツに応じた構造化データ提案"""

    SCHEMA_BY_BUSINESS_TYPE = {
        "ec_retail": {
            "primary": ["Product", "Offer", "AggregateRating"],
            "secondary": ["Organization", "BreadcrumbList"],
            "benefits": {
                "simple": "商品が検索結果にリッチに表示され、価格・評価が見えます",
                "detail": "構造化データを設定することで、検索結果にリッチリザルト（価格、在庫、レビュー星数）が表示されやすくなります。"
            }
        },
        "healthcare": {
            "primary": ["MedicalOrganization", "Physician", "MedicalClinic"],
            "secondary": ["FAQPage", "LocalBusiness"],
            "benefits": {
                "simple": "診療時間や医師の情報が分かりやすく表示されます",
                "detail": "信頼性の高い医療情報として検索エンジンに認識されやすくなります。"
            }
        },
        "restaurant": {
            "primary": ["Restaurant", "Menu", "MenuItem"],
            "secondary": ["LocalBusiness", "AggregateRating"],
            "benefits": {
                "simple": "メニューや営業時間が検索結果から確認できるようになります",
                "detail": "Googleマップや検索結果での視認性が大幅に向上します。"
            }
        },
        "article": {
            "primary": ["Article", "NewsArticle", "BlogPosting"],
            "secondary": ["Person", "Organization", "BreadcrumbList"],
            "benefits": {
                "simple": "記事の著者や公開日が正しく表示されます",
                "detail": "ニュース枠への掲載や、検索結果でのアイキャッチ表示に寄与します。"
            }
        },
        "corporate": {
            "primary": ["Organization", "WebSite"],
            "secondary": ["BreadcrumbList", "FAQPage"],
            "benefits": {
                "simple": "会社情報やサイト情報が正しく伝わります",
                "detail": "企業情報の信頼性が高まり、検索結果の表示品質向上に寄与します。"
            }
        }
    }

    def suggest_schemas(self, business_type: str, content_analysis: Dict) -> List[Dict]:
        """最適な構造化データを提案"""
        suggestion = self.SCHEMA_BY_BUSINESS_TYPE.get(
            business_type,
            self.SCHEMA_BY_BUSINESS_TYPE.get("article")
        )

        results = []
        for schema_type in suggestion.get("primary", []):
            results.append({
                "schema_type": schema_type,
                "priority": "primary",
                "benefit": suggestion.get("benefits", {})
            })
        for schema_type in suggestion.get("secondary", []):
            results.append({
                "schema_type": schema_type,
                "priority": "secondary",
                "benefit": suggestion.get("benefits", {})
            })

        existing = analyze_existing_schema(content_analysis.get("json_ld", []))
        if existing.get("types"):
            for item in results:
                if item["schema_type"] in existing["types"]:
                    item["already_present"] = True

        return results


SCHEMA_TEMPLATES = {
    "Product": {
        "template": '''{{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{product_name}",
  "description": "{description}",
  "image": "{image_url}",
  "brand": {{
    "@type": "Brand",
    "name": "{brand_name}"
  }},
  "offers": {{
    "@type": "Offer",
    "price": "{price}",
    "priceCurrency": "JPY",
    "availability": "https://schema.org/InStock"
  }}
}}''',
        "required_fields": ["name", "offers"],
        "recommended_fields": ["description", "image", "brand", "aggregateRating"]
    },
    "LocalBusiness": {
        "template": '''{{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "{business_name}",
  "address": "{address}",
  "telephone": "{telephone}",
  "openingHours": "{opening_hours}",
  "url": "{url}"
}}''',
        "required_fields": ["name", "address"],
        "recommended_fields": ["telephone", "openingHours", "url"]
    },
    "Article": {
        "template": '''{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{headline}",
  "datePublished": "{date_published}",
  "author": {{
    "@type": "Person",
    "name": "{author_name}"
  }},
  "image": "{image_url}",
  "publisher": {{
    "@type": "Organization",
    "name": "{publisher_name}"
  }}
}}''',
        "required_fields": ["headline", "datePublished"],
        "recommended_fields": ["author", "image", "publisher"]
    },
    "FAQPage": {
        "template": '''{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {{
      "@type": "Question",
      "name": "{question}",
      "acceptedAnswer": {{
        "@type": "Answer",
        "text": "{answer}"
      }}
    }}
  ]
}}''',
        "required_fields": ["mainEntity"],
        "recommended_fields": ["acceptedAnswer"]
    }
}


def generate_schema_template(schema_type: str, page_data: Dict) -> str:
    """ページデータを元にカスタマイズしたテンプレートを生成"""
    template_data = SCHEMA_TEMPLATES.get(schema_type)
    if not template_data:
        return ""

    template = template_data["template"]
    defaults = {
        "product_name": page_data.get("title", "商品名"),
        "description": page_data.get("description", "商品の説明文"),
        "image_url": page_data.get("image", "https://example.com/image.jpg"),
        "brand_name": page_data.get("brand", "ブランド名"),
        "price": page_data.get("price", "0"),
        "business_name": page_data.get("name", "店舗名"),
        "address": page_data.get("address", "住所"),
        "telephone": page_data.get("telephone", "00-0000-0000"),
        "opening_hours": page_data.get("opening_hours", "Mo-Sa 10:00-18:00"),
        "url": page_data.get("url", "https://example.com"),
        "headline": page_data.get("title", "記事タイトル"),
        "date_published": page_data.get("date_published", "2025-01-01"),
        "author_name": page_data.get("author", "著者名"),
        "publisher_name": page_data.get("publisher", "運営者名"),
        "question": page_data.get("question", "よくある質問"),
        "answer": page_data.get("answer", "回答内容")
    }

    return template.format(**defaults)


def analyze_existing_schema(json_ld: List[Dict]) -> Dict:
    """既存の構造化データを分析"""
    types = []
    for item in json_ld:
        if not isinstance(item, dict):
            continue
        item_type = item.get("@type")
        if isinstance(item_type, list):
            types.extend(item_type)
        elif item_type:
            types.append(item_type)

    unique_types = sorted(set(types))
    return {
        "types": unique_types,
        "count": len(types)
    }


def validate_schema(schema: Dict) -> Dict:
    """構造化データの妥当性チェック"""
    if not isinstance(schema, dict):
        return {"valid": False, "issues": ["schemaはdictである必要があります"]}

    schema_type = schema.get("@type")
    if not schema_type:
        return {"valid": False, "issues": ["@typeがありません"]}

    template = SCHEMA_TEMPLATES.get(schema_type)
    if not template:
        return {"valid": True, "issues": []}

    issues = []
    for field in template.get("required_fields", []):
        if field not in schema:
            issues.append(f"必須フィールドがありません: {field}")

    return {
        "valid": len(issues) == 0,
        "issues": issues
    }
