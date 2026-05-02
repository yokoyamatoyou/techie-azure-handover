# Phase 04: ビジネス目標パーソナライズ

優先度: 🟡 中
状態: ✅ 完了

---

## 背景・目的

現状のパーソナライズ入力は「業界・URLタイプ・CMS」のみ。
**ビジネス目標（何を達成したいか）** によって改善アクションの優先順位が変わるべきだが、
現状はすべてのサイトに同じ優先順位で改善案を出している。

### 目標選択 → 改善優先順位の対応

| ビジネス目標 | 最優先改善カテゴリ |
|------------|-----------------|
| 🔍 オーガニック流入増加 | SEO（キーワード最適化・構造化データ） |
| 💡 AI検索（GEO）での引用増加 | AIO（E-E-A-T・TL;DR・統計密度） |
| 📈 CV率・リード獲得 | CTA明確化・FAQ・信頼性 |
| 🏷️ ブランド認知・指名検索強化 | エンティティ・構造化データ・E-E-A-T |
| ⚡ サイト技術健全性 | Core Web Vitals・セキュリティ・クロール |

---

## 実装内容

### 変更1: `nicegui_app.py` — ビジネス目標セレクタ追加

業界セレクタの下に追加（L990付近）：

```python
ui.label("ビジネス目標").classes("input-label")
goal_select = ui.select(
    options=[
        "自動判定",
        "オーガニック流入増加（SEO優先）",
        "AI検索での引用増加（GEO/AIO優先）",
        "CV率・リード獲得（CTA改善優先）",
        "ブランド認知・指名検索強化",
        "サイト技術健全性（エンジニア優先）",
    ],
    value="自動判定",
    label="目標を選択（任意）",
).classes("w-full")
```

### 変更2: `nicegui_app.py` — goal_value を analyze_url() に渡す

```python
goal_value = goal_select.value or "自動判定"
# analyze_url() の引数に追加
result = await run.io_bound(
    state.analyzer.analyze_url,
    url_value,
    industry_value,
    balance_value,
    deep_value,
    platform_value,
    url_type_value,
    goal_value,   # ← 追加
)
```

### 変更3: `core/engine/orchestrator.py` — analyze_url() シグネチャ拡張

```python
def analyze_url(
    self,
    url,
    user_industry=None,
    balance=50,
    deep=True,
    platform=None,
    url_type=None,
    business_goal="自動判定",   # ← 追加
):
```

### 変更4: `core/engine/orchestrator.py` — goal に基づいて decision_actions をソート

`decision_actions` リストを返す前に、ビジネス目標に応じてソートする：

```python
GOAL_PRIORITY_KEYS = {
    "オーガニック流入増加（SEO優先）":    ["seo", "findability", "structure"],
    "AI検索での引用増加（GEO/AIO優先）": ["aio", "geo", "eeat", "tldr"],
    "CV率・リード獲得（CTA改善優先）":   ["cta", "trust", "faq", "compliance"],
    "ブランド認知・指名検索強化":          ["entity", "eeat", "schema", "trust"],
    "サイト技術健全性（エンジニア優先）":  ["cwv", "security", "engineer", "technical"],
}

def _sort_actions_by_goal(actions: list, business_goal: str) -> list:
    priority_keys = GOAL_PRIORITY_KEYS.get(business_goal, [])
    if not priority_keys:
        return actions  # 自動判定はソートなし

    def _score(action: dict) -> int:
        tags = str(action.get("category", "") + action.get("type", "") + action.get("kpi", "")).lower()
        for i, key in enumerate(priority_keys):
            if key in tags:
                return -i   # 優先キーが前にあるほど高スコア
        return 1  # 優先外は後ろ

    return sorted(actions, key=_score)

# decision_actions 生成後に適用
decision_actions = _sort_actions_by_goal(decision_actions, business_goal)
```

### 変更5: `core/ui/reports/executive_summary.py` — 目標をサマリー冒頭に表示

```python
# ui.label("経営サマリー...") の直後
if integrated.get("business_goal") and integrated["business_goal"] != "自動判定":
    ui.label(f"目標: {integrated['business_goal']}").classes("card-hint text-blue-600 font-bold")
```

---

## 対象ファイル

| ファイル | 変更箇所 |
|---------|---------|
| `nicegui_app.py` | goal_select UI追加（L990付近）+ analyze_url 呼び出し（L1313付近） |
| `core/engine/orchestrator.py` | `analyze_url()` シグネチャ + `_sort_actions_by_goal()` 追加 |
| `core/ui/reports/executive_summary.py` | 目標テキスト表示追加 |
| `WORKLOG.md` | 完了記録追記 |

---

## 完了条件

- [ ] `py_compile` 全変更ファイルエラーなし
- [ ] UI に「ビジネス目標」セレクタが表示される
- [ ] 「AI検索での引用増加」を選ぶと decision_actions の上位が AIO/GEO 関連になる
- [ ] 「自動判定」のときは従来の順序が維持される
- [ ] 経営サマリーに選択した目標が表示される
- [ ] WORKLOG.md 更新

---

## 注意事項

- `business_goal` は結果 dict に含めて UI に渡す（`last_analysis_results["business_goal"] = business_goal`）
- ソートは安定ソート（同スコアのアクションは元の順序を保持）
- `GOAL_PRIORITY_KEYS` のキーは各 action の `category`・`type`・`kpi` フィールドとの部分一致で判定
  → action 生成側のフィールド値を確認してからキーワードを調整すること
- 「自動判定」選択時は一切変更しない（後方互換性を保つ）
