from pathlib import Path
import sys

out_path = Path(r"C:\notecode\note\tests\generation_check.txt")

try:
    sys.path.insert(0, r"C:\notecode")
    from note.article_fetcher import FetchedContent
    from note.article_generator import ArticleGenerator

    contexts = [FetchedContent(title="テスト", content="AIは社会に影響を与える。倫理的な配慮が必要。")]

    gen = ArticleGenerator()
    res = gen.generate(contexts, "初心者向けに", "ai")
    title = res.get("title", "")
    lead = (res.get("lead", "") or "").replace("\n", " ")
    hashtags = res.get("hashtags", "")
    body_len = len(res.get("body", ""))
    out_path.write_text(
        "\n".join([
            f"TITLE: {title}",
            f"LEAD: {lead[:160]}",
            f"HASHTAGS: {hashtags}",
            f"BODY_LEN: {body_len}",
        ]),
        encoding="utf-8",
    )
except Exception as e:
    out_path.write_text(f"ERROR: {e}", encoding="utf-8")
