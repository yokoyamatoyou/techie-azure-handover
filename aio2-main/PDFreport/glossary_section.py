# -*- coding: utf-8 -*-
"""
PDF Glossary Section - 専門用語の平易な解説

読者が理解しやすいよう、技術用語を一般的な言葉で説明するセクションを生成する。
"""

from typing import Dict, List, Any, Optional

# 専門用語 → 平易な説明のマッピング
GLOSSARY_TERMS: Dict[str, Dict[str, str]] = {
    "エンティティ": {
        "short": "固有名詞（人名・会社名・製品名など）",
        "long": "Googleなどの検索エンジンが「何について書かれているか」を理解するための手がかりとなる具体的な名前です。人名、会社名、地名、製品名などが該当します。",
        "example": "例: 「トヨタ自動車」「東京都」「iPhone」など",
    },
    "JSON-LD": {
        "short": "検索エンジン向けの情報タグ（名刺のようなもの）",
        "long": "ページの内容を検索エンジンに正確に伝えるための機械可読形式です。人間には見えませんが、AIや検索エンジンがページの構造を理解するのに役立ちます。",
        "example": "例: 「このページは〇〇会社の商品ページで、価格は△△円です」という情報を機械に伝えます",
    },
    "PID（情報密度）": {
        "short": "文章の濃さ（無駄な言葉が少ないか）",
        "long": "Propositional Idea Densityの略。文章中の「意味のある単語」の割合を示します。無駄な言い回しが少なく、内容が濃い文章ほどスコアが高くなります。",
        "example": "例: 「非常に大変素晴らしい」より「優れている」の方が情報密度が高い",
    },
    "E-E-A-T": {
        "short": "経験・専門性・権威性・信頼性（Googleが重視する品質指標）",
        "long": "Experience（経験）、Expertise（専門性）、Authoritativeness（権威性）、Trustworthiness（信頼性）の頭文字。Googleがコンテンツの品質を評価する際の重要な基準です。",
        "example": "例: 医療情報は医師が書いた方がE-E-A-Tが高い",
    },
    "OGP": {
        "short": "SNSでシェアされた時の見た目を決める設定",
        "long": "Open Graph Protocolの略。TwitterやFacebookでURLをシェアした際に表示されるタイトル、説明文、画像を指定するためのタグです。",
        "example": "例: LINEでURLを送った時に表示されるサムネイル画像とタイトル",
    },
    "robots.txt": {
        "short": "検索エンジンへの「ここは見ていいよ/ダメよ」の指示書",
        "long": "ウェブサイトのルートに置くテキストファイルで、検索エンジンのクローラー（巡回プログラム）にアクセスを許可/禁止するページを指示します。",
        "example": "例: 管理画面や開発中のページをGoogleに見せないようにする",
    },
    "構造化データ": {
        "short": "検索エンジンが理解しやすい形式で書かれた情報",
        "long": "ページの内容（商品価格、レビュー評価、イベント日時など）を、人間だけでなく機械も読み取れる形式で記述したものです。検索結果でリッチリザルト（評価★など）として表示されることがあります。",
        "example": "例: 検索結果に表示される料理レシピの調理時間やカロリー",
    },
    "AIO（AI Optimization）": {
        "short": "AI検索エンジン向けの最適化",
        "long": "ChatGPT、Bing Copilot、PerplexityなどのAI検索エンジンに引用されやすくするための対策。従来のSEOに加えて、AIが理解・引用しやすい構造を意識します。",
        "example": "例: 結論を先に書く、定義を明確にする、出典を明記する",
    },
    "スキーマ": {
        "short": "ページの種類を示すラベル（Article、Product、FAQなど）",
        "long": "schema.orgで定義された語彙を使って、ページの種類や内容を検索エンジンに伝えるためのマークアップです。",
        "example": "例: 「このページは商品ページです」「このページはFAQです」",
    },
    "メタディスクリプション": {
        "short": "検索結果に表示されるページの説明文",
        "long": "HTMLのhead内に記述する説明文で、検索結果のタイトル下に表示されることがあります。クリック率に影響する重要な要素です。",
        "example": "例: Googleで検索した時にタイトルの下に表示される2-3行の説明",
    },
}


def get_glossary_section_data(
    terms_to_include: Optional[List[str]] = None,
    format_type: str = "short"
) -> List[Dict[str, str]]:
    """
    PDFやUIに表示する用語集データを取得する。
    
    Args:
        terms_to_include: 含める用語のリスト（Noneの場合は全用語）
        format_type: "short" または "long"
    
    Returns:
        用語と説明のリスト
    """
    result = []
    terms = terms_to_include or list(GLOSSARY_TERMS.keys())
    
    for term in terms:
        if term in GLOSSARY_TERMS:
            entry = GLOSSARY_TERMS[term]
            result.append({
                "term": term,
                "description": entry.get(format_type, entry["short"]),
                "example": entry.get("example", ""),
            })
    
    return result


def render_glossary_section(pdf, max_terms: int = 10) -> None:
    """
    PDFに用語集セクションを描画する。
    
    Args:
        pdf: HighQualityReportPDF インスタンス
        max_terms: 表示する最大用語数
    """
    glossary_data = get_glossary_section_data(format_type="short")[:max_terms]
    
    if not glossary_data:
        return
    
    pdf.add_page()
    pdf.add_section_title("用語集（専門用語の解説）")
    
    for item in glossary_data:
        term = item["term"]
        description = item["description"]
        example = item.get("example", "")
        
        # 用語ボックスとして表示
        content = f"{description}"
        if example:
            content += f"\n{example}"
        
        pdf.add_info_card(
            term,
            content,
            card_color=(240, 248, 255),  # AliceBlue - 薄い青
            max_chars=300,
            allow_split=False,
        )


def get_term_tooltip(term: str) -> str:
    """
    UI用のツールチップテキストを取得する。
    
    Args:
        term: 用語名
    
    Returns:
        短い説明文（ツールチップ用）
    """
    if term in GLOSSARY_TERMS:
        return GLOSSARY_TERMS[term]["short"]
    return ""


def format_term_with_tooltip(term: str) -> Dict[str, str]:
    """
    用語にツールチップ情報を付加する（UI用）。
    
    Args:
        term: 用語名
    
    Returns:
        用語とツールチップ情報を含む辞書
    """
    return {
        "term": term,
        "tooltip": get_term_tooltip(term),
        "has_tooltip": term in GLOSSARY_TERMS,
    }
