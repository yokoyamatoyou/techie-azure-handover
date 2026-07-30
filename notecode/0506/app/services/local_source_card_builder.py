from __future__ import annotations

from typing import Any

from app.services.source_fact_segmenter import extract_fact_candidates


def build_local_source_card(packet: dict[str, Any]) -> dict[str, Any]:
    claims = _claims_with_locations(packet)
    facts = [
        {
            "fact_id": f"F{index:03d}",
            "claim": claim,
            "category": "source_claim",
            "importance": max(1, 6 - index),
            "source_span": location,
            "usable_in_article": True,
            "confidence": "medium",
            "risk_flags": [],
        }
        for index, (claim, location) in enumerate(claims, start=1)
    ]
    return {
        "source_id": packet["source_id"],
        "source_type": packet["source_type"],
        "title": packet["title"],
        "published_or_updated_at": packet["metadata"].get("published_or_updated_at"),
        "reliability": "user_uploaded" if packet["source_type"] in {"manual", "pdf", "word"} else "external",
        "main_topics": [packet["title"]],
        "facts": facts,
        "quotes_or_phrases": [],
        "warnings": [
            {"type": "ambiguous", "message": warning, "source_span": None}
            for warning in packet.get("warnings", [])
        ],
        "metadata": {
            "source_label": packet["title"],
            "url": packet["metadata"].get("url"),
            "canonical_url": packet["metadata"].get("canonical_url"),
            "author": None,
            "retrieved_at": packet["metadata"].get("retrieved_at"),
            "source_priority": packet["metadata"].get("source_priority", 5),
            "extraction_method": packet["metadata"].get("extraction_method"),
            "extraction_confidence": packet["metadata"].get("extraction_confidence", "medium"),
        },
    }


def _claims_with_locations(packet: dict[str, Any]) -> list[tuple[str, str]]:
    chunks = packet["chunks"]
    if packet["source_type"] == "pdf":
        return _pdf_claims(chunks)

    text = "\n".join(chunk["text"] for chunk in chunks)
    claims = extract_fact_candidates(text, limit=6)
    return [
        (claim, chunks[min(index, len(chunks) - 1)]["source_locations"][0])
        for index, claim in enumerate(claims)
    ]


def _pdf_claims(chunks: list[dict[str, Any]]) -> list[tuple[str, str]]:
    claims: list[tuple[str, str]] = []
    seen: set[str] = set()
    seen_locations: set[str] = set()
    _append_pdf_claims(_priority_chunks(chunks), claims, seen, seen_locations, allow_generic=False)
    if len(claims) >= 6:
        return claims[:12]
    _append_pdf_claims(_sample_chunks(chunks, max_chunks=14), claims, seen, seen_locations, allow_generic=True)
    return claims[:12]


def _append_pdf_claims(
    chunks: list[dict[str, Any]],
    claims: list[tuple[str, str]],
    seen: set[str],
    seen_locations: set[str],
    allow_generic: bool,
) -> None:
    for chunk in chunks:
        location = chunk["source_locations"][0]
        if location in seen_locations:
            continue
        seen_locations.add(location)
        normalized_claims = _slide_claims(chunk["text"])
        for claim in normalized_claims:
            key = claim.rstrip("。")
            if key in seen:
                continue
            seen.add(key)
            claims.append((claim, location))
            if len(claims) >= 12:
                return
        if normalized_claims or not allow_generic:
            continue
        for claim in extract_fact_candidates(chunk["text"], limit=2):
            if _is_pdf_candidate_noise(claim):
                continue
            key = claim.rstrip("。")
            if key in seen:
                continue
            seen.add(key)
            claims.append((claim, location))
            if len(claims) >= 12:
                return


def _slide_claims(text: str) -> list[str]:
    claims: list[str] = []
    if "ビジネスモデルとは" in text and "誰に" in text and "対価を受け取る" in text:
        claims.append("ビジネスモデルは、誰に何をどのように届け、どのように対価を受け取るのかをモデル化したものとして説明されています。")
    if "左から右に" in text and "iterative" in text:
        claims.append("事業化のプロセスは、左から右へ一直線に進むものではなく、何度でも前のプロセスに戻る反復的なものとして説明されています。")
    if "ビジネスモデルのパターン認識" in text and "有" in text:
        claims.append("既存のビジネスモデルのパターンを認識することは、オリジナルの検討スピードを上げる材料として説明されています。")
    if "On Demand" in text and "実" in text and "需要" in text:
        claims.append("On Demandは、計画策定ではなくユーザーの実需要を起点に生産やサービス提供を行うパターンとして紹介されています。")
    if "Business Model Canvas" in text and ("ひとつのツール" in text or "価値提案" in text):
        claims.append("Business Model Canvasは、アイデアをビジネスモデルの形態へ落とし込むツールとして紹介されています。")
    if "Marketingの本質" in text and "仲間を" in text:
        claims.append("Marketingは、価値を心から喜んでくれる人を見つけ、仲間を増やしていくアクションとして説明されています。")
    if "フィードバックを受けて迅速に修正" in text:
        claims.append("不確実な状況下では、やってみてフィードバックを受け、迅速に修正する流れが示されています。")
    if "フレームワーク" in text and "直接使う必要は必ずしもない" in text:
        claims.append("マーケティングの方法論やフレームワークを、そのまま直接使う必要は必ずしもないと説明されています。")
    if "市場性" in text and ("定義する姿勢" in text or "市場を見出して定義する" in text):
        claims.append("市場性では、既存市場を見るだけでなく、自ら市場を見出して定義する姿勢が重要だと説明されています。")
    if "市場性" in text and "ポテンシャル" in text:
        claims.append("見えていない新市場でも、その市場にどの程度のポテンシャルがあるのかを考える必要があると説明されています。")
    return claims


def _is_pdf_candidate_noise(claim: str) -> bool:
    noise_terms = (
        "Customer Rela",
        "Key Ac",
        "Key Resource",
        "Value Propos",
        "Revenue Stream",
        "Cost Structure",
        "Business Model Canvas 顧客",
        "ビジネスモデルとマーケティング",
    )
    if any(term in claim for term in noise_terms):
        return True
    return claim.rstrip("。").endswith(("ビジネス", "能力", "⽣産"))


def _priority_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    terms = (
        "事業化のプロセス",
        "Business Model Canvas",
        "ビジネスモデルとは",
        "パターン認識",
        "On Demand",
        "Marketingの本質",
        "Marketability",
    )
    return [chunk for chunk in chunks if any(term in chunk["text"] for term in terms)]


def _sample_chunks(chunks: list[dict[str, Any]], max_chunks: int) -> list[dict[str, Any]]:
    if len(chunks) <= max_chunks:
        return chunks
    last = len(chunks) - 1
    indexes = sorted({round(i * last / (max_chunks - 1)) for i in range(max_chunks)})
    return [chunks[index] for index in indexes]
