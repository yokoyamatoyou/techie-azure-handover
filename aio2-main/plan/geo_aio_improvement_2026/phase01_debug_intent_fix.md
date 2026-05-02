# Phase 01: 緊急修正 — DEBUGプリント除去 + Intent係数修正

優先度: 🔴 高
状態: ✅ 完了（2026-02-27）
依存: なし（他Phaseより先に実施）

---

## 背景・根拠

### 問題A: DEBUGプリントの本番混入

`core/scoring_engine.py` L118〜127 に `print()` デバッグ出力が残存。
本番ログを汚染し、大量アクセス時にはパフォーマンス劣化の原因になる。

```python
# 現行（削除対象）
print("\n[DEBUG] ========== ScoringEngine統合 ==========")
print(f"[DEBUG] SEO score (before boost): {seo_results.get('total_score', 0.0)}")
...（計9行）
```

### 問題B: Intent係数の方向性が2025年AI検索環境と逆転

```python
# 現行
INTENT_ALPHA = {
    "transactional":  0.8,   # SEO重視
    "informational":  0.3,   # SEO軽視 → AIO重視になるはずが実装が逆
    "navigational":   1.0,   # SEO最重視
    "unknown":        0.5,
}
```

`α = SEO weight` として計算しているため `informational=0.3` は
「SEO30%:AIO70%」という意味になる。
**これ自体は正しい方向だが、2025年時点では係数値がまだ保守的すぎる。**

実態：
- 2025年7月時点でGoogle AIOの表示率39.2%（informationalクエリで特に高い）
- informationalクエリのAIO引用率は transactional の約7倍
- 推奨値: `informational: 0.2`（SEO20%:AIO80%）

また `navigational=1.0`（SEO100%:AIO0%）は
指名検索でもAI Overviewが表示される現状と乖離。

---

## 変更内容

### 変更1: DEBUGプリントをlogging.debugに差し替え

**対象ファイル:** `core/scoring_engine.py` L118〜127

**変更前:**
```python
# ========== DEBUG: ペナルティ適用後のスコア ==========
print("\n[DEBUG] ========== ScoringEngine統合 ==========")
print(f"[DEBUG] SEO score (before boost): {seo_results.get('total_score', 0.0)}")
print(f"[DEBUG] AIO score (before boost): {aio_results.get('total_score', 0.0)}")
print(f"[DEBUG] SEO score (after boost): {seo_score}")
print(f"[DEBUG] AIO score (after boost): {aio_score}")
print(f"[DEBUG] AIO score (after penalty): {aio_score_after_penalty}")
print(f"[DEBUG] Penalties applied: {penalty_warnings}")
print(f"[DEBUG] SEO weight: {seo_weight}, AIO weight: {aio_weight}")
print("[DEBUG] ==========================================\n")
```

**変更後:**
```python
logger.debug(
    "ScoringEngine統合: SEO=%.1f→%.1f AIO=%.1f→%.1f(penalty後=%.1f) "
    "weight=SEO%.2f/AIO%.2f penalties=%s",
    seo_results.get("total_score", 0.0), seo_score,
    aio_results.get("total_score", 0.0), aio_score,
    aio_score_after_penalty,
    seo_weight, aio_weight,
    penalty_warnings,
)
```

`scoring_engine.py` の先頭付近に `import logging` と
`logger = logging.getLogger(__name__)` を追加する。

---

### 変更2: Intent係数の更新

**対象ファイル:** `core/scoring_engine.py` L8〜13

**変更前:**
```python
INTENT_ALPHA = {
    "transactional": 0.8,
    "informational": 0.3,
    "navigational": 1.0,
    "unknown": 0.5,
}
```

**変更後:**
```python
INTENT_ALPHA = {
    # α = SEO比率（1-α = AIO比率）
    # 2025年9月 Google AIモード日本語対応・AIO表示率39.2%を反映
    "transactional": 0.7,   # 購買意図: SEO70% / AIO30%（従来0.8）
    "informational": 0.2,   # 情報収集: SEO20% / AIO80%（従来0.3）
    "navigational":  0.8,   # 指名検索: SEO80% / AIO20%（従来1.0 → AIO0%は現実と乖離）
    "unknown":       0.5,   # 不明: 50:50
}
```

**変更理由コメントを同ファイルの定数直上に追記:**
```python
# Intent係数α: α = SEO比率、(1-α) = AIO比率
# 2026-02-27改訂: Google AIモード日本語対応(2025/9)後の実態値に調整
# informational: AIO表示率が高く引用が支配的 → AIO80%
# transactional: 購買クエリはSEOが依然有効だが AIO30% を確保
# navigational:  指名検索でもAIO表示あり → AIO20% を確保（旧値0%は不適切）
```

---

## 完了条件

- [ ] `python -m py_compile core/scoring_engine.py` がエラーなし
- [ ] `grep -n "print.*DEBUG" core/scoring_engine.py` が0件
- [ ] `import logging` と `logger = logging.getLogger(__name__)` が追加されている
- [ ] `INTENT_ALPHA["informational"]` が `0.2` になっている
- [ ] `INTENT_ALPHA["navigational"]` が `0.8` になっている
- [ ] 変更理由コメントが定数直上に記載されている

---

## 注意事項

- `INTENT_ALPHA` は `scoring_engine.py` 内のみで使用。他ファイルへの影響なし（`grep -r "INTENT_ALPHA" core/` で確認）
- DEBUGブロック除去により `integrate()` 関数の行番号がずれる。他ファイルからの参照なし（プロキシ経由）
- WORKLOG更新: Phase完了後に `aio2-main/WORKLOG.md` に記録
