from __future__ import annotations

from typing import Any


def render_local_draft(article_brief: dict[str, Any], knowledge_pack: dict[str, Any]) -> str:
    brief = article_brief["article_brief"]
    claims = knowledge_pack["article_knowledge_pack"]["confirmed_facts"]
    claim_by_id = {claim["claim_id"]: claim for claim in claims}
    lines: list[str] = []

    lines.extend([f"# {_render_article_title(brief)}", ""])
    for section_index, section in enumerate(brief["sections"], start=1):
        lines.extend([f"## {section['heading']}", ""])
        if section_index == 1:
            lines.append(_render_opening_sentence(brief, claim_by_id, section["assigned_claim_ids"]))
            lines.append("")
        elif brief.get("genre_id") == "market_explanation":
            lines.append(_render_market_section_intro(section["heading"]))
            lines.append("")
        for claim_id in section["assigned_claim_ids"]:
            claim = claim_by_id.get(claim_id)
            if not claim:
                continue
            sentence = render_claim_sentence(claim["preferred_expression"], brief["narrator"], brief.get("genre_id"))
            if sentence:
                lines.append(sentence)
                lines.append("")

    lines.append(_render_closing_sentence(brief))
    return "\n".join(lines).strip()


def _render_article_title(brief: dict[str, Any]) -> str:
    explicit = str(brief.get("title") or brief.get("article_title") or "").strip()
    if explicit:
        return explicit.lstrip("#").strip()
    genre_id = brief.get("genre_id")
    if genre_id == "market_explanation":
        return "事業化と市場の見方を整理する"
    if genre_id == "announcement":
        return "お知らせ"
    if genre_id == "case_study":
        return "事例から見える取り組み"
    if genre_id == "comparison_guide":
        return "選び方を整理する"
    if genre_id == "daily_activity":
        return "日々の取り組みから"
    if brief.get("narrator") == "当社":
        return "当社の取り組みについて"
    return "私たちの取り組みについて"


def render_claim_sentence(expression: str, narrator: str = "私たち", genre_id: str | None = None) -> str:
    text = _clean_expression(expression)
    if not text:
        return ""
    if genre_id == "market_explanation":
        return _render_market_claim_sentence(text)
    if text.endswith(("。", "！", "？", "!", "?")) and not _is_fragment_like(text):
        return _align_narrator(text, narrator)
    return _complete_fragment(text, narrator)


def _render_opening_sentence(
    brief: dict[str, Any],
    claim_by_id: dict[str, dict[str, Any]],
    assigned_claim_ids: list[str],
) -> str:
    narrator = brief["narrator"]
    joined = "。".join(
        claim_by_id[claim_id]["preferred_expression"]
        for claim_id in assigned_claim_ids
        if claim_id in claim_by_id
    )
    if "データ" in joined and ("京都" in joined or "京都工業" in joined):
        return f"{narrator}は京都で、データ入力やデジタル化に関する相談と向き合ってきました。"
    if brief.get("genre_id") == "market_explanation":
        return (
            f"{narrator}はこの資料から、事業化の考え方を整理します。"
            "アイデアそのものだけでなく、価値の届け方と市場の見立て方まで分けて扱います。"
        )
    return f"{narrator}が取り組んでいることを、少し具体的に紹介します。"


def _render_closing_sentence(brief: dict[str, Any]) -> str:
    if brief.get("genre_id") == "market_explanation":
        return "まずは身近な事業を一つ選び、誰に何を届けるのか、市場をどう見立てるのかを言葉にしてみる。そうしてから資料に戻ると、論点が自分ごとに近づくはずです。"
    return "データの扱いに迷ったときは、小さなことでもご相談ください。"


def _render_market_section_intro(heading: str) -> str:
    if "マーケティング" in heading:
        return "ここからは、価値を届ける相手との関係をどう育てるかに目を向けます。"
    if "市場性" in heading:
        return "市場性は、既にある市場を眺めるだけではなく、市場をどう定義するかにも関わる論点です。"
    return ""


def _render_market_claim_sentence(text: str) -> str:
    stripped = text.rstrip("。")
    if "事業化のプロセス" in stripped and "反復" in stripped:
        return "事業化のプロセスは、一直線に進むものというより、何度も前の論点に戻りながら進めるものです。考え直しが入る前提で見ると、アイデア検討の動き方も少し現実に近づきます。"
    if "誰に何をどのように届け" in stripped:
        return "ビジネスモデルでは、誰に、何を、どのように届けるのかを分けて考えます。さらに、どのように対価を受け取るのかまで含めて、事業の形を整理します。"
    if "パターンを認識" in stripped:
        return "既存のビジネスモデルのパターンを知っておくと、ゼロから考える負担を減らせます。オリジナルな案を考える前に、似た構造を知っておくことが発想の下地になります。"
    if "On Demand" in stripped:
        return "On Demandは、計画を先に固めるよりも、ユーザーの実需要を起点に生産やサービス提供を組み立てる見方です。需要の出方を見ながら動くため、作りすぎや機会損失を考える論点にもなります。"
    if "Business Model Canvas" in stripped:
        return "Business Model Canvasは、アイデアをビジネスモデルの形に落とし込むための道具です。頭の中の構想を、顧客、価値、チャネル、収益などの要素に分けて置いてみる使い方です。"
    if "Marketing" in stripped or "仲間を増やしていく" in stripped:
        return "マーケティングは、単に売るための手順ではなく、価値を喜んでくれる人を見つけ、仲間を増やしていく動きです。最初の理解者をどう見つけるかが、成長を考える論点になります。"
    if "フィードバック" in stripped:
        return "不確実な状況では、最初から正解を当てにいくより、まず試して反応を見ることが重要になります。フィードバックを受けて素早く直す流れまで含めて、マーケティングを捉える形です。"
    if "フレームワーク" in stripped:
        return "方法論やフレームワークは便利ですが、そのまま当てはめればよいという話ではありません。目の前の価値と相手に合わせて、使う部分を選ぶ姿勢が求められます。"
    if "市場性" in stripped and "定義する姿勢" in stripped:
        return "市場性を見るときは、既存市場の情報を集めるだけでは足りない場合があります。新しいアイデアでは、まだ見えていない市場を検討する側が見出し、定義していく姿勢も必要になります。"
    if "ポテンシャル" in stripped:
        return "まだはっきり見えていない市場でも、どれくらいの可能性があるのかを考える必要があります。市場が見えないから考えないのではなく、見えにくいからこそ仮説を置いて確かめる、という読み方です。"
    return _complete_fragment(stripped, "私たち")


def _clean_expression(expression: str) -> str:
    return " ".join(line.strip() for line in expression.splitlines() if line.strip()).strip(" 。")


def _align_narrator(text: str, narrator: str) -> str:
    return text.replace("弊社", narrator).replace("私達", narrator)


def _is_fragment_like(text: str) -> bool:
    stripped = text.rstrip("。")
    if len(stripped) <= 18:
        return True
    return stripped.endswith(("相談", "実績", "総合力", "一貫対応", "サポート"))


def _complete_fragment(text: str, narrator: str) -> str:
    stripped = _align_narrator(text.rstrip("。"), narrator)
    if stripped in {"Business Model Canvas", "ビジネスモデルとは？", "ビジネスモデル"}:
        return "ビジネスモデルは、価値を誰に、どのような形で届けるかを整理する視点です。"
    if stripped in {"Marketingの本質", "マーケティングの本質"}:
        return "マーケティングでは、最初に喜んでくれる人との関係を広げていく視点が示されています。"
    if stripped.startswith("市場性") or "Marketability" in stripped:
        return "市場性は、既にある市場を見るだけでなく、自ら市場を見出して定義する考え方として示されています。"
    if "仲間を増やしていく" in stripped:
        return "マーケティングの本質は、価値を理解してくれる仲間を増やしていくことだと整理されています。"
    if "データで可能性を創造する" in stripped:
        return "「データで可能性を創造する」という言葉を掲げています。"
    if stripped.startswith("小さなことからでも"):
        return ""
    if stripped.endswith("伝統と革新が同居する古都"):
        return "伝統と革新が同居する京都から、データ化やデジタル化を支援しています。"
    if stripped == "データ活用の目的はあるがやり方がわからない":
        return "データ活用の目的はあるものの、進め方が分からないという相談に対応しています。"
    if stripped == "データの集計・収集から分析まで一手に任せたい":
        return "データの集計・収集から分析まで任せたいという相談にも対応しています。"
    if stripped.endswith("一貫対応"):
        return f"{stripped}しています。"
    if stripped.endswith("実績"):
        return f"{stripped}があります。"
    if stripped.endswith("ご相談"):
        return f"{stripped}を受けています。"
    if stripped.endswith("総合力"):
        return f"{stripped}を強みとしています。"
    if stripped.endswith("サポート"):
        return f"{stripped}しています。"
    if stripped.endswith("センター"):
        return f"{stripped}として事業を行っています。"
    if stripped.endswith("お悩みに対して対応します"):
        return "データ活用に関するお悩みに対応しています。"
    return f"{stripped}。"
