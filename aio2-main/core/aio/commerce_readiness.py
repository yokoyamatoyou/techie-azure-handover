from __future__ import annotations

import re
from typing import Any, Dict, List

from bs4 import BeautifulSoup


def assess_openai_commerce_readiness(soup: BeautifulSoup) -> Dict[str, Any]:
    html = str(soup).lower()
    product_schema = 0
    offer_schema = 0

    for script in soup.find_all("script", {"type": "application/ld+json"}):
        raw = script.string or ""
        lowered = raw.lower()
        if '"@type"' not in lowered:
            continue
        if any(token in lowered for token in ['"product"', '"@type":"product"', '"@type": "product"']):
            product_schema += 1
        if any(token in lowered for token in ['"offer"', '"aggregateoffer"']):
            offer_schema += 1

    text = soup.get_text(" ", strip=True)
    price_present = bool(re.search(r"(¥|\$|€|price|価格)\s*[\d,]+", text, re.IGNORECASE))
    availability_present = bool(re.search(r"(in[_ -]?stock|out[_ -]?of[_ -]?stock|在庫あり|在庫切れ|残り\d+点)", text, re.IGNORECASE))
    add_to_cart_present = bool(re.search(r"(add to cart|buy now|カートに追加|購入する)", text, re.IGNORECASE))
    image_count = len(soup.find_all("img"))

    product_like = bool(product_schema or offer_schema or (price_present and (availability_present or add_to_cart_present)))
    platform_hint = "shopify" if "shopify" in html else ("etsy" if "etsy" in html else None)

    signals = {
        "product_schema_count": product_schema,
        "offer_schema_count": offer_schema,
        "price_present": price_present,
        "availability_present": availability_present,
        "add_to_cart_present": add_to_cart_present,
        "image_count": image_count,
        "platform_hint": platform_hint,
    }

    if not product_like:
        return {
            "status": "informational",
            "applicable": False,
            "signals": signals,
            "summary": "商品ページ信号が弱いため、merchant feed readiness は高優先ではありません。",
            "notes": [],
        }

    notes: List[str] = []
    if not product_schema:
        notes.append("Product schema が見つからず、商品データの整形度が低い可能性があります。")
    if not price_present:
        notes.append("価格シグナルが弱く、商品比較結果での精度に不利です。")
    if not availability_present:
        notes.append("在庫・販売可否シグナルが弱く、最新 availability を伝えにくい状態です。")
    if image_count == 0:
        notes.append("商品画像が見つかりません。視覚的な商品比較に不利です。")
    if platform_hint in {"shopify", "etsy"}:
        notes.append(f"{platform_hint.title()} は OpenAI merchants page で既存カタログ連携対象として案内されています。")

    status = "pass" if len(notes) <= 1 else "warn"
    summary = "商品データの主要シグナルは概ね揃っています。"
    if status == "warn":
        summary = "商品ページですが、merchant feed / product data の整形を強める余地があります。"

    return {
        "status": status,
        "applicable": True,
        "signals": signals,
        "summary": summary,
        "notes": notes,
    }


def build_perplexity_operational_note() -> Dict[str, Any]:
    return {
        "status": "informational",
        "summary": "Perplexity docs は robots.txt 許可に加え、公開IPレンジを source of truth として WAF allowlist に使うことを案内しています。",
        "notes": [
            "HTML だけでは Cloudflare / AWS WAF の allowlist 状態は確認できません。",
            "PerplexityBot と Perplexity-User の両方について、最新 IP JSON endpoint を運用確認対象にしてください。",
        ],
        "ip_json_endpoints": [
            "https://www.perplexity.com/perplexitybot.json",
            "https://www.perplexity.com/perplexity-user.json",
        ],
    }
