# Phase 04: スコア体系の精緻化（YMYL修正 + GEOスコア独立表示）

優先度: 🟡 中
状態: ✅ 完了（2026-02-27）
依存: P03完了後（GEOスコアが存在することが前提）

---

## 背景・根拠

### 問題A: YMYL 業界のaio_boostが不適切

```python
# 現行
INDUSTRY_PROFILES = {
    "ymyl": {"aio_boost": 1.0, "seo_boost": 1.0},  # 何もしない
}
```

YMYL（医療/金融/法務）は2025年のAI検索で:
- E-E-A-Tが充足していればAIOに積極的に引用（ヘルスケア系の引用率は高い）
- E-E-A-Tが不足していればAI filteringで完全除外
- 「常にaio_boost=1.0」は「YMYLを一般サイトと同じ扱い」≒ 誤評価

**修正方針**: E-E-A-Tスコア（P02で改善済み）に応じてブーストorペナルティを動的適用。

### 問題B: GEOスコアがAIOに内包されていて見えにくい

P03でGEOスコアを追加したが、UIではAIOタブ内のサブ指標として表示。
Semrush 2025年版は「GEO最適化スコア」を独立した評価軸として提示している。

**修正方針**: GEOスコアを統合サマリーの独立カードとして表示。

---

## 変更内容

### 変更A: YMYL動的ブースト（`scoring_engine.py`）

**対象:** `INDUSTRY_PROFILES` の `ymyl` エントリ + `_apply_industry_boost()` ロジック

```python
# 変更後: ymylはE-E-A-Tスコアに応じて動的計算
INDUSTRY_PROFILES = {
    "b2b saas": {"aio_boost": 1.2, "seo_boost": 1.0},
    "real estate": {"aio_boost": 1.1, "seo_boost": 1.1},
    "ecommerce": {"aio_boost": 1.0, "seo_boost": 1.3},
    # ymylは静的値を削除し、_apply_industry_boost()内で動的計算
}

YMYL_KEYWORDS = ["医療", "健康", "医薬", "金融", "保険", "投資", "法律", "弁護", "裁判"]
```

```python
def _apply_industry_boost(
    self,
    seo_score: float,
    aio_score: float,
    industry: Optional[str],
    eeat_score: float = 0.0,   # ← 新規引数（P02のeeat_scoreを受け取る）
) -> tuple[float, float]:
    if not industry:
        return seo_score, aio_score
    key = industry.lower()

    # YMYL動的ブースト
    if any(kw in (industry or "") for kw in YMYL_KEYWORDS):
        if eeat_score >= 7.0:
            # E-E-A-T充足: AIOブースト（引用されやすい）
            return seo_score * 1.0, aio_score * 1.2
        elif eeat_score >= 4.0:
            # E-E-A-T中程度: 変化なし
            return seo_score, aio_score
        else:
            # E-E-A-T不足: AIOペナルティ（AI filteringで除外リスク）
            return seo_score * 1.0, aio_score * 0.7

    # 通常業界（既存ロジック）
    profile = None
    for cand, cfg in self.industry_profiles.items():
        if cand in key:
            profile = cfg
            break
    if not profile:
        return seo_score, aio_score
    return seo_score * profile.get("seo_boost", 1.0), aio_score * profile.get("aio_boost", 1.0)
```

`integrate()` の呼び出し箇所も引数追加:
```python
eeat_score = float((aio_results.get("scores", {}).get("eeat") or {}).get("score", 0.0))
seo_score, aio_score = self._apply_industry_boost(seo_score, aio_score, ctx.industry, eeat_score)
```

---

### 変更B: GEOスコード独立カード（UI）

**対象:** `core/ui/reports/executive_summary.py`（経営サマリー）

現行の経営サマリーには SEO/AIO スコアのみ表示。
GEOスコードを3列目のカードとして追加:

```
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│  SEO スコア  │  │  AIO スコア  │  │  GEO スコア（新）│
│    72 / 100  │  │    65 / 100  │  │     55 / 100     │
│ Google検索対応│  │ AI引用対応   │  │ 生成AI最適化     │
└──────────────┘  └──────────────┘  └──────────────────┘
```

GEOスコア計算式（`scoring_engine.py` の `integrate()` に追加）:
```python
# GEOスコア = TL;DR(40%) + 統計密度(35%) + E-E-A-T(25%) の加重平均 × 10
geo_tldr_score   = float((aio_results.get("scores", {}).get("geo_tldr") or {}).get("score", 0.0))
geo_stats_score  = float((aio_results.get("scores", {}).get("geo_stats") or {}).get("score", 0.0))
eeat_score_norm  = eeat_score  # 既にP02で取得済み

geo_score = (
    geo_tldr_score  * 0.40 +
    geo_stats_score * 0.35 +
    eeat_score_norm * 0.25
)
# geo_tldr は0〜5なので10点スケールに正規化
geo_score_100 = min(100.0, (
    (geo_tldr_score / 5.0) * 40.0 +   # TL;DR: 40点満点
    (geo_stats_score / 10.0) * 35.0 +  # 統計密度: 35点満点
    (eeat_score_norm / 10.0) * 25.0    # E-E-A-T: 25点満点
))
```

`integrate()` の返り値に追加:
```python
"geo_score": round(geo_score_100, 1),
"geo_breakdown": {
    "tldr": round(geo_tldr_score, 2),
    "stats_density": round(geo_stats_score, 2),
    "eeat": round(eeat_score_norm, 2),
},
```

---

## 完了条件

- [ ] `python -m py_compile core/scoring_engine.py` がエラーなし
- [ ] YMYL業界でeeat_score=8.0の時に `aio_boost=1.2` が適用される
- [ ] YMYL業界でeeat_score=2.0の時に `aio_boost=0.7` が適用される（ペナルティ）
- [ ] `integrate()` の返り値に `"geo_score"` キーが存在する
- [ ] 経営サマリーにGEOスコードカードが表示される
- [ ] WORKLOG更新

---

## 注意事項

- `_apply_industry_boost()` に `eeat_score` 引数を追加するため、
  呼び出し元（`integrate()`）のシグネチャも変更。単一呼び出し元なので影響範囲は限定的。
- YMYL判定キーワードは日本語のみ。英語表記（"medical", "healthcare"等）は
  既存 `INDUSTRY_PROFILES` 側で対応するため追加不要。
- GEOスコア100点スケールは暫定値。実ユーザーデータ取得後に重みを調整する。
