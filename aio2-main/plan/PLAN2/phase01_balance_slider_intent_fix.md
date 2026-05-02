# Phase 01: バランスSliderバグ修正 + Intent alpha 復活

優先度: 🔴 高
状態: ✅ 完了

---

## 背景・問題

### バグの内容

UIには「SEO <-> AIO バランス」スライダー（0〜100）があるが、
**スライダーの値がスコア計算に反映されていない** かつ
**intent係数α（クエリ意図による自動重み）が常に無効化されている**。

### 根本原因

`core/scoring_engine.py` の `ScoreContext` データクラスのデフォルト値が原因：

```python
# 現状（バグあり）
@dataclass
class ScoreContext:
    intent: str = "unknown"
    industry: Optional[str] = None
    seo_weight: float = 0.5      # ← Noneでなく0.5がデフォルト
    aio_weight: float = 0.5      # ← Noneでなく0.5がデフォルト
    url_type: Optional[str] = None
```

下流の重み適用ロジック（`integrate()` メソッド内）：

```python
# seo_weight は 0.5（not None）なので常に ctx の値を使う
seo_weight = ctx.seo_weight if ctx.seo_weight is not None else alpha
aio_weight = ctx.aio_weight if ctx.aio_weight is not None else 1 - alpha

# この条件は永遠に False → intent alpha が一切適用されない
if ctx.seo_weight is None and ctx.aio_weight is None:
    seo_weight = alpha
    aio_weight = 1 - alpha
```

### 影響

`INTENT_ALPHA` に設定されている以下の値が**完全に無視**されている：

```python
INTENT_ALPHA = {
    "transactional": 0.7,   # 購買意図: SEO70% / AIO30%
    "informational": 0.2,   # 情報収集: SEO20% / AIO80%  ← 最重要
    "navigational":  0.8,   # 指名検索: SEO80% / AIO20%
    "unknown":       0.5,
}
```

情報収集クエリ（informational）は AIO80% で計算されるべきだが、
現状は常に 50:50 になっている。

---

## 修正内容

### 変更1: `core/scoring_engine.py` — ScoreContext のデフォルト値を None に変更

```python
# 修正後
@dataclass
class ScoreContext:
    intent: str = "unknown"
    industry: Optional[str] = None
    seo_weight: Optional[float] = None   # None = intent alpha に従う
    aio_weight: Optional[float] = None   # None = intent alpha に従う
    url_type: Optional[str] = None
```

### 変更2: `core/engine/orchestrator.py` — balance=50 のとき None を渡す

```python
# _integrate_results() の呼び出し前（analyze_url メソッド内）
# balance=50 はデフォルト値 = ユーザーが明示指定していない → intent alpha に委ねる

seo_weight = (100 - balance) / 100
aio_weight = balance / 100

# balance が 50 ちょうどの場合は None にして intent alpha を使わせる
if balance == 50:
    seo_weight = None
    aio_weight = None

integrated_results = self._integrate_results(
    seo_results=...,
    aio_results=...,
    seo_weight=seo_weight,
    aio_weight=aio_weight,
    ...
)
```

### 変更3（任意・推奨）: `nicegui_app.py` — スライダーに "自動" 表示を追加

スライダーが 50 のとき「自動（意図に基づく）」を表示することで、
ユーザーが「なぜ 50/50 じゃないのか」と混乱しないようにする。

```python
# balance_slider の下に説明ラベルを追加
balance_label = ui.label("自動（クエリ意図に基づき調整）").classes("card-hint")

def _update_balance_label():
    v = int(balance_slider.value or 50)
    if v == 50:
        balance_label.text = "自動（クエリ意図に基づき調整）"
    else:
        seo_pct = 100 - v
        aio_pct = v
        balance_label.text = f"手動設定: SEO {seo_pct}% / AIO {aio_pct}%"

balance_slider.on("update:model-value", lambda _: _update_balance_label())
```

---

## 対象ファイル

| ファイル | 変更箇所 |
|---------|---------|
| `core/scoring_engine.py` | `ScoreContext` クラス（L51〜58）のデフォルト値 |
| `core/engine/orchestrator.py` | `analyze_url()` 内の `_integrate_results()` 呼び出し前（L1064付近）|
| `nicegui_app.py` | `balance_slider` 定義付近（L1025〜1028）|

---

## 完了条件

- [ ] `py -m py_compile core/scoring_engine.py core/engine/orchestrator.py nicegui_app.py` がエラーなし
- [ ] intent="informational" の場合に `integrated_results["alpha"]` が 0.2 になる
- [ ] intent="transactional" の場合に `integrated_results["alpha"]` が 0.7 になる
- [ ] balance=70 を明示した場合は seo_weight=0.3、aio_weight=0.7 になる
- [ ] balance=50（デフォルト）の場合は alpha が informational=0.2 に従う
- [ ] WORKLOG.md 更新

---

## 検証方法（簡易）

```python
from core.scoring_engine import ScoringEngine, ScoreContext

engine = ScoringEngine()
ctx = ScoreContext(intent="informational")   # seo_weight=None
result = engine.integrate(
    {"total_score": 60, "scores": {}},
    {"total_score": 40, "scores": {}},
    ctx
)
assert abs(result["alpha"] - 0.2) < 0.01, f"Expected 0.2, got {result['alpha']}"
print("OK: informational alpha = 0.2")
```

---

## 注意事項

- `ScoreContext.seo_weight` を `Optional[float]` に変更すると、
  他の呼び出し箇所（`_integrate_results` の引数）も型チェック的に影響を受ける可能性あり。
  `py_compile` でなく `mypy` を使っている場合は警告が出るかもしれないが、動作上は問題なし。
- balance=50 を「自動」とする設計は、ユーザーが明示的に 50 を選んだ場合も
  「自動」として扱う。厳密な分離が必要であれば「自動/手動」切替トグルを追加する。
