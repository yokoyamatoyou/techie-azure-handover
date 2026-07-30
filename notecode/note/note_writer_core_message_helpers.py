"""Pure core-message UI text helpers for note writer."""
from __future__ import annotations


def _build_core_message_placeholder(
    article_type_key: str,
    semantic_article_key: str = "",
    content_goal_key: str = "",
) -> str:
    semantic_key = str(semantic_article_key or "").strip()
    article_key = str(article_type_key or "").strip()
    goal_key = str(content_goal_key or "").strip()
    if semantic_key == "company_introduction":
        return "例: 事業内容と運用支援の姿勢を根拠付きで伝える"
    if article_key == "announcement":
        return "例: 変更点と必要な対応を迷わず把握できるようにする"
    if article_key == "case_study":
        return "例: どこで迷い、何を変え、どの条件で再現できるかを伝える"
    if goal_key == "trust":
        return "例: 判断材料と根拠が自然に伝わるようにする"
    return "例: 初期設定の負担を減らし、導入判断を進めやすくする価値を伝える"


def _build_core_message_helper_text(
    article_type_key: str,
    semantic_article_key: str = "",
    content_goal_key: str = "",
) -> str:
    semantic_key = str(semantic_article_key or "").strip()
    article_key = str(article_type_key or "").strip()
    goal_key = str(content_goal_key or "").strip()
    if semantic_key == "company_introduction":
        return "※会社紹介では必須です。事業内容の説明ではなく、この会社の何を伝え切るかを1文で入れてください。"
    if article_key == "announcement":
        return "※お知らせで目的を選んだ場合に入力してください。変更点の要約ではなく、読後に何を迷わせないかを1文で入れます。"
    if article_key == "case_study":
        return "※事例で目的を選んだ場合に入力してください。成功談ではなく、読者に残す学びや再現条件を1文で入れます。"
    if article_key == "branding" and goal_key:
        return "※ブランド記事で目的を選んだ場合に入力してください。紹介文全体で押し出す判断軸を1文で入れます。"
    return "※核メッセージは、ブランド / 事例 / お知らせで目的を選んだ場合だけ表示します。"


def _requires_core_message_input(article_type_key: str, content_goal_key: str) -> bool:
    type_key = str(article_type_key or "").strip()
    goal_key = str(content_goal_key or "").strip()
    return type_key in {"branding", "case_study", "announcement"} and goal_key not in {"", "auto"}
