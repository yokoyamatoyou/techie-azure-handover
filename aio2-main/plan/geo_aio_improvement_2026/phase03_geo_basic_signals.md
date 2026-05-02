# Phase 03: GEO基本指標の追加（TL;DR検出 + 統計密度スコア）

優先度: 🟠 中高
状態: ✅ 完了（2026-02-27）
依存: P02完了後推奨（`aio_analyzer.py` 改変後に追加）

---

## 背景・根拠

ACM SIGKDD 2024採択論文「GEO: Generative Engine Optimization」の実証:
- **統計・数値の引用密度** → +30〜40% AI可視性向上
- **冒頭要約（TL;DR）の有無** → AIO引用スニペットの直接候補
- **FAQPage JSON-LD** → AIO引用率3.2倍（既実装済み✅）

現行コトミガキは上記2点（TL;DR・統計密度）を**一切スコア化していない**。

---

## 変更内容

### 新規関数1: `detect_tldr_summary()` — 冒頭要約検出

AIが引用しやすい「冒頭50〜70字の要約ブロック」の有無と品質を評価する。

```python
# 検出パターン
TLDR_INDICATORS = [
    # 明示的TL;DR
    r"(TL;?DR|要約|まとめ|ポイント|この記事(で)?わかること)",
    # 箇条書き冒頭（先頭300字以内に箇条書きがある）
    # 冒頭段落が50〜150字の要約的短文
]

def detect_tldr_summary(self, text: str, soup: BeautifulSoup) -> dict:
    """
    冒頭要約（TL;DR）の有無と品質を検出する。
    Returns:
        {
            "score": float(0〜5),
            "has_explicit_tldr": bool,       # 「要約」「TL;DR」等の明示ラベルあり
            "has_early_bullets": bool,        # 先頭300字以内に箇条書きあり
            "lead_paragraph_length": int,     # 冒頭段落の文字数
            "is_optimal_length": bool,        # 50〜150字なら最適
            "advice": str,
        }
    """
    body_text = text[:2000]  # 先頭2000字のみ評価

    # 明示TL;DRラベル検出
    has_explicit = bool(re.search(
        r"(TL;?DR|要約|まとめ(ると)?|この記事(の|で)?ポイント|わかること)",
        body_text[:500], re.IGNORECASE
    ))

    # 先頭300字内の箇条書き（li/ul要素）
    early_section = str(soup)[:3000]
    has_early_bullets = bool(re.search(r"<(ul|ol|li)\b", early_section))

    # 冒頭段落の長さ
    paragraphs = [p for p in soup.find_all("p") if len(p.get_text(strip=True)) > 20]
    lead_len = len(paragraphs[0].get_text(strip=True)) if paragraphs else 0
    is_optimal = 50 <= lead_len <= 150

    # スコア計算（最大5点）
    score = 0.0
    if has_explicit:
        score += 3.0
    elif has_early_bullets:
        score += 2.0
    if is_optimal:
        score += 2.0
    elif lead_len > 0:
        score += 0.5

    score = min(5.0, score)

    # アドバイス文
    if score < 2.0:
        advice = "冒頭に「この記事でわかること」などの要約ブロック（50〜150字）を追加するとAIに引用されやすくなります"
    elif score < 4.0:
        advice = "冒頭要約はありますが、明示ラベル（例: 「この記事のポイント」）を加えるとさらに効果的です"
    else:
        advice = "冒頭要約は最適化されています"

    return {
        "score": round(score, 2),
        "has_explicit_tldr": has_explicit,
        "has_early_bullets": has_early_bullets,
        "lead_paragraph_length": lead_len,
        "is_optimal_length": is_optimal,
        "advice": advice,
    }
```

---

### 新規関数2: `calculate_statistics_density()` — 統計・数値密度スコア

GEO論文で +30〜40% 可視性向上が実証された「数値・統計・比較表現の密度」を評価する。

```python
# 検出パターン（日本語数値表現）
STATISTICS_PATTERNS = [
    r"[0-9０-９]+\s*(%|％|倍|件|人|社|年|か月|ヶ月|万|億|兆)",     # 数値+単位
    r"[0-9０-９]+\s*[〜~]\s*[0-9０-９]+",                           # 範囲表現
    r"(約|およそ|最大|最小|平均|中央値)\s*[0-9０-９]",               # 修飾付き数値
    r"(前年比|前月比|対前年|YoY|比較|増加|減少|上昇|下落)\s*[0-9０-９]", # 比較
    r"調査(によると|では|の結果)|アンケート|統計|データ(によると|では)", # 調査出典
    r"(出典|参考|引用)\s*[:：]",                                    # 外部引用
]

def calculate_statistics_density(self, text: str) -> dict:
    """
    本文中の統計・数値・引用密度を評価する。
    Returns:
        {
            "score": float(0〜10),
            "stats_count": int,        # 数値/統計表現の総検出数
            "chars_per_stat": float,   # 1統計あたりの文字数（密度指標）
            "has_citations": bool,     # 「出典：」「参考：」等の引用表記あり
            "density_level": str,      # "high" / "medium" / "low"
        }
    """
    total_chars = len(text)
    if total_chars == 0:
        return {"score": 0.0, "stats_count": 0, "chars_per_stat": 0, "has_citations": False, "density_level": "low"}

    hits = []
    for pat in STATISTICS_PATTERNS:
        hits.extend(re.findall(pat, text))

    stats_count = len(hits)
    has_citations = bool(re.search(r"(出典|参考文献|引用)\s*[:：]", text))

    # 密度: 1000字あたりの統計表現数
    density_per_1k = stats_count / (total_chars / 1000)

    # スコア計算（上限10点）
    # 密度 ≥ 3.0/千字: 高密度（8〜10点）
    # 密度 ≥ 1.5/千字: 中密度（5〜7点）
    # 密度 ≥ 0.5/千字: 低密度（2〜4点）
    if density_per_1k >= 3.0:
        score = 8.0 + min(2.0, (density_per_1k - 3.0) * 0.5)
        level = "high"
    elif density_per_1k >= 1.5:
        score = 5.0 + (density_per_1k - 1.5) * 2.0
        level = "medium"
    elif density_per_1k >= 0.5:
        score = 2.0 + (density_per_1k - 0.5) * 3.0
        level = "low"
    else:
        score = density_per_1k * 4.0
        level = "low"

    # 出典表記ボーナス
    if has_citations:
        score = min(10.0, score + 1.0)

    chars_per_stat = round(total_chars / stats_count, 1) if stats_count > 0 else 0.0

    return {
        "score": round(min(10.0, score), 2),
        "stats_count": stats_count,
        "chars_per_stat": chars_per_stat,
        "has_citations": has_citations,
        "density_level": level,
    }
```

---

## AIOスコアへの組み込み

`aio_analyzer.py` の `analyze()` 内、`citation_readiness` の後に追加:

```python
# Phase 3: GEO基本指標
tldr_result = self.detect_tldr_summary(text, soup)
stats_density = self.calculate_statistics_density(text)
```

`scores` ディクショナリに追加:
```python
"geo_tldr":       {"score": tldr_result["score"],     "detail": tldr_result},
"geo_stats":      {"score": stats_density["score"],    "detail": stats_density},
```

`total_score` の重み付け（既存スコアに追加。既存ウェイトは調整不要でGEO軸として並列）:
```python
# GEOスコアは total_score に5%ずつ寄与（既存スコアから各0.5%ずつ削減）
geo_contribution = (tldr_result["score"] * 0.05 + stats_density["score"] * 0.05)
```

---

## UI表示の追加

`core/ui/tabs/aio_tab.py` にGEOセクションを追加:

```
📊 GEO（生成AI引用最適化）スコア
  冒頭要約（TL;DR）: 3.5 / 5
    ✅ 冒頭箇条書きあり
    ℹ️ 明示ラベル（「この記事のポイント」等）を追加するとさらに効果的
  統計・数値密度: 6.0 / 10
    検出: 12件 / 1.8件/千字（中程度）
    ✅ 出典表記あり
```

---

## 完了条件

- [ ] `python -m py_compile core/aio_analyzer.py` がエラーなし
- [ ] `detect_tldr_summary()` が `text=""`・空soupで `score=0.0` を返す（エラーなし）
- [ ] 「この記事でわかること」を含むテキストで `has_explicit_tldr=True`
- [ ] 「30%増加」「調査によると」を含むテキストで `stats_count > 0`
- [ ] UIのAIOタブにGEOセクションが表示される
- [ ] WORKLOG更新

---

## 注意事項

- GEOスコアは `total_score` への寄与を小さく（5%×2=10%）抑え、既存スコアを壊さない
- `detect_tldr_summary()` は先頭2000字のみ処理（パフォーマンス）
- 統計密度の閾値（3.0/千字等）は初期値。実運用後に `generation_parameter_tuning_log.md` 相当で調整
