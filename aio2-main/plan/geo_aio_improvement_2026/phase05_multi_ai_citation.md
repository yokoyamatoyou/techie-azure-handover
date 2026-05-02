# Phase 05: 多AI対応 — プラットフォーム別引用予測

優先度: 🟡 中
状態: ✅ 完了（2026-02-27）
依存: P03・P04完了後（GEO指標・E-E-A-Tが揃ってから評価可能）

---

## 背景・根拠

### 現状のコトミガキの限界

現行の AIO 評価は「Google AI Overviews」を主対象として設計。
しかし 2025年時点の AI検索プラットフォームは分散化している:

| プラットフォーム | 日本シェア | 引用特性 |
|----------------|-----------|---------|
| ChatGPT (SearchGPT) | 82.2% | Bing上位87%と一致・深い専門性重視 |
| Perplexity | 6.2% | UGC含む多ソース・平均21.9源/回答 |
| Google AI Mode | 増加中（2025/9〜日本語対応） | E-E-A-T前提・構造化データ重視 |
| Gemini | 5.3% | Googleエコシステム内評価 |

各プラットフォームで**引用されやすいコンテンツ特性が異なる**にも関わらず、
現行は一律の AIO スコアしか返せていない。

---

## 変更内容

### 新規関数: `estimate_platform_citation()` を `aio_analyzer.py` に追加

既存の分析結果を基に、各プラットフォームの引用確率を推定する。
**実際にAPIを叩くのではなく、既存スコアのルールベース推定**。

```python
def estimate_platform_citation(
    self,
    eeat_score: float,
    structure_score: float,
    stats_density_score: float,
    tldr_score: float,
    faq_detected: bool,
    llms_txt_score: float,
    word_count: int,
) -> dict:
    """
    各AIプラットフォームへの引用適合度を推定する。
    Returns:
        {
            "google_aio": {"score": float, "level": str, "key_factors": list},
            "chatgpt":    {"score": float, "level": str, "key_factors": list},
            "perplexity": {"score": float, "level": str, "key_factors": list},
            "overall":    {"score": float, "level": str},
        }
    """

    def _level(score: float) -> str:
        if score >= 70: return "高"
        if score >= 40: return "中"
        return "低"

    # --- Google AI Overview ---
    # 重視: E-E-A-T(強), 構造化データ(強), FAQ JSON-LD(強), 冒頭要約(中)
    google_score = min(100.0, (
        eeat_score      * 3.5 +   # 35点満点（最重要）
        structure_score * 2.5 +   # 25点満点
        (10.0 if faq_detected else 0.0) * 2.0 +  # 20点満点
        tldr_score      * 4.0     # 20点満点（tldr 0〜5 → 20点）
    ))
    google_factors = []
    if eeat_score < 5: google_factors.append("E-E-A-T不足")
    if not faq_detected: google_factors.append("FAQコンテンツなし")
    if tldr_score < 2: google_factors.append("冒頭要約なし")

    # --- ChatGPT (SearchGPT) ---
    # 重視: コンテンツ深度(word_count強), 統計密度(強), 権威性(E-E-A-T中)
    # Bingインデックスと強相関 → 技術的SEOが重要
    chatgpt_score = min(100.0, (
        min(1.0, word_count / 2000) * 30.0 +   # 文字量: 30点満点（2000字で満点）
        stats_density_score * 3.0 +              # 統計密度: 30点満点
        eeat_score          * 2.5 +              # E-E-A-T: 25点満点
        structure_score     * 1.5                # 構造: 15点満点
    ))
    chatgpt_factors = []
    if word_count < 800: chatgpt_factors.append("コンテンツ量が少ない（目安800字以上）")
    if stats_density_score < 4: chatgpt_factors.append("数値・統計が少ない")
    if eeat_score < 4: chatgpt_factors.append("著者/組織情報が不明瞭")

    # --- Perplexity ---
    # 重視: 複数ソース引用(citations強), FAQ(中), llms.txt(中), UGC的リッチさ
    perplexity_score = min(100.0, (
        stats_density_score * 2.5 +          # 統計密度（外部引用含む）: 25点
        (llms_txt_score / 10.0) * 20.0 +     # llms.txt品質: 20点
        (10.0 if faq_detected else 0.0) * 1.5 +  # FAQ: 15点
        structure_score     * 2.0 +           # 構造: 20点
        eeat_score          * 2.0             # E-E-A-T: 20点
    ))
    perplexity_factors = []
    if llms_txt_score < 5: perplexity_factors.append("llms.txtの品質改善")
    if stats_density_score < 3: perplexity_factors.append("引用・出典の追加")
    if not faq_detected: perplexity_factors.append("FAQ形式コンテンツの追加")

    # 総合（加重平均: Google40% / ChatGPT35% / Perplexity25%）
    overall_score = google_score * 0.40 + chatgpt_score * 0.35 + perplexity_score * 0.25

    return {
        "google_aio":  {"score": round(google_score, 1),  "level": _level(google_score),  "key_factors": google_factors},
        "chatgpt":     {"score": round(chatgpt_score, 1),  "level": _level(chatgpt_score),  "key_factors": chatgpt_factors},
        "perplexity":  {"score": round(perplexity_score, 1), "level": _level(perplexity_score), "key_factors": perplexity_factors},
        "overall":     {"score": round(overall_score, 1),  "level": _level(overall_score)},
    }
```

---

## UI表示（新規タブ or サブセクション）

`core/ui/tabs/aio_tab.py` のGEOセクション内にプラットフォーム別表示を追加:

```
🤖 プラットフォーム別 引用適合度（推定）

  Google AI Mode:   ████████░░ 78点 [高]
    ✅ E-E-A-T良好  ✅ FAQ検出済み  ℹ️ 冒頭要約を追加するとさらに良い

  ChatGPT:          ██████░░░░ 61点 [中]
    ℹ️ 数値・統計が少ない（目安: 1000字あたり2件以上）

  Perplexity:       █████░░░░░ 52点 [中]
    ℹ️ llms.txtの品質改善  ℹ️ 引用・出典の追加
```

---

## アドバイス生成（`aio_suggestions.py`）

プラットフォーム別の低スコア因子に応じたアドバイスを追加:

```python
PLATFORM_ADVICE_TEMPLATES = {
    "google_aio": {
        "E-E-A-T不足": "著者の氏名・資格をページ内に明記し、schema.org/Personを実装してください",
        "FAQコンテンツなし": "ページ下部にFAQセクションを追加し、FAQPage JSON-LDを実装してください",
        "冒頭要約なし": "ページ先頭に「この記事でわかること」等の要約ブロック（50〜150字）を追加してください",
    },
    "chatgpt": {
        "コンテンツ量が少ない（目安800字以上）": "ChatGPTに引用されるには最低800字以上のコンテンツ量が推奨されます",
        "数値・統計が少ない": "具体的な数値・割合・調査データを追加すると引用率が高まります（例: 「利用者の73%が…」）",
        "著者/組織情報が不明瞭": "会社概要ページへのリンクと著者情報を本文またはフッターに追加してください",
    },
    "perplexity": {
        "llms.txtの品質改善": "llms.txtを最適化してPerplexityのクローラーに主要ページを案内してください",
        "引用・出典の追加": "「出典：〇〇調査（2025年）」のような外部引用を本文に含めてください",
        "FAQ形式コンテンツの追加": "Q&A形式のコンテンツをPerplexityは好む傾向があります",
    },
}
```

---

## 完了条件

- [ ] `python -m py_compile core/aio_analyzer.py` がエラーなし
- [ ] `estimate_platform_citation()` が全引数0/Falseで `overall.score >= 0` を返す（エラーなし）
- [ ] eeat_score=8, faq_detected=True の場合に `google_aio.level == "高"` になる
- [ ] word_count=300 の場合に `chatgpt.key_factors` に文字量警告が入る
- [ ] UIに3プラットフォームの推定スコアが表示される
- [ ] 各プラットフォームの low スコア因子に対応するアドバイスが表示される
- [ ] WORKLOG更新

---

## 注意事項

- 「推定」であることをUIで明示する（「実際のAIシステムへのアクセスに基づくものではありません」）
- スコアはルールベースの近似値。A/Bテストや実データで定期的に調整する
- Google AI Mode日本語対応が2025年9月〜のため、国内サイトへの適用精度は今後上昇の余地あり
- 重みパラメータ（Google40%等）は `config.toml` に外出しして調整可能にすることを推奨
