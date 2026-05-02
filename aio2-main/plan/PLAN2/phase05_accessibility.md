# Phase 05: アクセシビリティ対応

優先度: 🟡 中
状態: ✅ 完了

---

## 背景・目的

現状、スコア表示に絵文字（🟢/🟡/🔴）を使っているが、
スクリーンリーダーは「緑の丸」「黄色の丸」「赤い丸」と読み上げるだけで意味が伝わらない。

また、NiceGUI のデフォルト UI には `aria-label` や `role` 属性がなく、
視覚障害者や企業の情報システムアクセシビリティ要件（JIS X 8341-3）を満たせない。

### 対応スコープ（最小限で効果的な範囲）

1. スコアゲージに aria-label 追加（数値と意味を明示）
2. ステータス絵文字に aria-label 追加
3. 重要なボタンに aria-label 追加

---

## 実装内容

### 変更1: `core/ui/reports/executive_summary.py` — ゲージに aria-label

NiceGUI の `ui.circular_progress` は Quasar の `q-circular-progress` をラップしており、
`.props()` メソッドで HTML 属性を追加できる。

```python
# 現状
with ui.circular_progress(
    value=value, min=0, max=100, size="80px",
    show_value=False, color=_gauge_color(value),
):
    ui.label(f"{value:.0f}").classes("text-base font-bold")

# 修正後
gauge = ui.circular_progress(
    value=value, min=0, max=100, size="80px",
    show_value=False, color=_gauge_color(value),
)
gauge.props(f'aria-label="{label}: {value:.0f}点 ({status_label})"')
with gauge:
    ui.label(f"{value:.0f}").classes("text-base font-bold")
```

### 変更2: `core/ui/reports/executive_summary.py` — GEO行の aria-label

```python
# linear_progress に aria-label 追加
ui.linear_progress(
    value=geo_score / 100, size="6px", show_value=False,
    color=_gauge_color(geo_score),
).classes("w-20").props(f'aria-label="GEOスコア: {geo_score:.0f}点"')
```

### 変更3: `core/ui/tabs/aio_tab.py` — プラットフォーム別バーの aria-label

```python
# for ループ内の linear_progress に追加
ui.linear_progress(
    value=score / 100, size="10px", show_value=False, color=bar_color,
).classes("flex-1").props(f'aria-label="{label}: {score:.0f}点 ({level})"')
```

### 変更4: `nicegui_app.py` — 分析ボタンに aria-label

```python
# 分析実行ボタン（既存コード）に .props() を追加
analyze_button = ui.button("分析実行", on_click=run_analysis).classes(...)
analyze_button.props('aria-label="URLを分析して SEO・AIOスコアを計算する"')
```

### 変更5: ステータス絵文字の代替テキスト規則（コーディング規約）

絵文字をそのまま使うのではなく、スクリーンリーダー向けに `role="img"` と `aria-label` を付与する。
ただし NiceGUI の `ui.label` は `<span>` タグであり、直接 role 指定が難しいため、
以下の「セーフパターン」を採用する：

```python
# セーフパターン: 絵文字を視覚専用にし、テキストも併記
ui.label(f"{status_symbol} {status_label}").classes("text-xs text-center")
# ↑ 例: "🟢 良好" → スクリーンリーダーは「緑の丸 良好」と読む → 意味が伝わる

# より厳密にするなら（span の aria-hidden で絵文字を隠す）は
# NiceGUI では .props('aria-hidden="true"') で対応可
```

---

## 対象ファイル

| ファイル | 変更箇所 |
|---------|---------|
| `core/ui/reports/executive_summary.py` | circular_progress, linear_progress に `.props(aria-label=...)` |
| `core/ui/tabs/aio_tab.py` | プラットフォーム別 linear_progress に `.props(aria-label=...)` |
| `nicegui_app.py` | 分析ボタンに `.props(aria-label=...)` |

---

## 完了条件

- [ ] `py_compile` 全変更ファイルエラーなし
- [ ] ブラウザの開発者ツール（Elements タブ）でゲージ要素に `aria-label` 属性が確認できる
- [ ] スクリーンリーダー（Windows Narrator 等）でスコアが「統合スコア: 72点 (要改善)」と読み上げられる
- [ ] WORKLOG.md 更新

---

## 注意事項

- NiceGUI の `.props()` メソッドは Quasar コンポーネントに HTML 属性を追加する
  - 例: `element.props('aria-label="説明"')`
  - 文字列内にダブルクォートが含まれる場合はシングルクォートでラップ（上記の通り）
- `aria-label` の文字列に `"` が含まれる場合はエスケープが必要（`&quot;` または `\'`）
- このフェーズは小変更の集合なので、他の Phase と並行して進めやすい
- JIS X 8341-3 完全準拠は本フェーズのスコープ外（まず主要コンポーネントのみ対応）
