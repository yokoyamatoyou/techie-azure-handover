# コトミガキ UI再設計 実装計画

**対象ファイル**: `C:\tetie\aio2-main\nicegui_app.py`（1,472行）
**フェーズ管理**: `C:\tetie\aio2-main\plan\ui_redesign_PROGRESS.md`
**参考実装**: `C:\tetie\notecode\note\note_writer_app.py`（notecodeで先行実装済み）

---

## ゴール（完成イメージ）

```
┌──────────────────────────────────────────┐
│  [HOME] | コトメイク | コトミガキ  ← 固定ナビ（黒・40px）
├──────────────────────────────────────────┤
│  ① URL入力 → ② 詳細設定 → ③ 分析結果   ← スティッキーバー（スクロールで固定）
├──────────────────────────────────────────┤
│ STEP 1 URL入力                           │ ← Card 1
│  [URL入力] [競合URL] [分析ボタン]        │
├──────────────────────────────────────────┤
│ STEP 2 詳細設定                          │ ← Card 2（現在のexpansion内容を独立カードへ）
│  業種 / プラットフォーム / 種別 / バランス│
│  進捗バー                                │
├──────────────────────────────────────────┤
│ STEP 3 分析結果 & 改善レポート           │ ← Card 3（分析完了後に表示）
│  [既存の results_panel + report_panel]   │
└──────────────────────────────────────────┘
```

---

## 現在のカード構造（変更前）

```
L882  with ui.card():          ← 入力カード（1枚）
L884      "分析起点"
L889      url_input + analyze_button
L892      competitor_input
L896      with ui.expansion("詳細設定"):  ← 折りたたみ
L899          industry_select
L921          platform_select
L927          url_type_select
L935          balance_slider
L939      status_label
L941      progress_label
L943      progress_bar
L946      loading

L986  results_container = ui.card()      ← 分析結果カード
L1060 report_container  = ui.card()      ← 改善レポートカード
```

---

## Phase 1: CSS追加

**場所**: L854 の `</style>` の直前（L853の後）

**追加するCSSブロック**（そのまま貼り付ける）:

```
      /* ---- STEP スティッキーバー ---- */
      .step-track {
        position: sticky;
        top: var(--nav-height);
        z-index: 500;
        background: rgba(255, 248, 245, 0.97);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-bottom: 1px solid var(--border);
        padding: 8px 0;
        display: flex !important;
        align-items: center;
        justify-content: center;
        gap: 10px;
      }
      .step-track-item {
        font-size: 12px;
        font-weight: 700;
        padding: 5px 16px;
        border-radius: 99px;
        transition: background 0.3s ease, color 0.3s ease;
        white-space: nowrap;
      }
      .step-track-active {
        background: var(--accent);
        color: white !important;
        box-shadow: 0 3px 10px rgba(232, 89, 12, 0.28);
      }
      .step-track-done {
        background: #D1FAE5;
        color: #065F46 !important;
      }
      .step-track-pending {
        background: #F3F4F6;
        color: #9CA3AF !important;
      }
```

**変更前の行**（L853-L856）:
```python
      .hub-nav .hub-nav-sep {
        color: #4F6070;
        font-size: 12px;
        user-select: none;
      }

    </style>
```

**変更後**（`</style>` の直前にCSSブロックを挿入）:
```python
      .hub-nav .hub-nav-sep {
        color: #4F6070;
        font-size: 12px;
        user-select: none;
      }

      /* ---- STEP スティッキーバー ---- */
      .step-track {
        position: sticky;
        top: var(--nav-height);
        z-index: 500;
        background: rgba(255, 248, 245, 0.97);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-bottom: 1px solid var(--border);
        padding: 8px 0;
        display: flex !important;
        align-items: center;
        justify-content: center;
        gap: 10px;
      }
      .step-track-item {
        font-size: 12px;
        font-weight: 700;
        padding: 5px 16px;
        border-radius: 99px;
        transition: background 0.3s ease, color 0.3s ease;
        white-space: nowrap;
      }
      .step-track-active {
        background: var(--accent);
        color: white !important;
        box-shadow: 0 3px 10px rgba(232, 89, 12, 0.28);
      }
      .step-track-done {
        background: #D1FAE5;
        color: #065F46 !important;
      }
      .step-track-pending {
        background: #F3F4F6;
        color: #9CA3AF !important;
      }

    </style>
```

---

## Phase 2: カード分割（3カード化）

### 概要

現在の1枚の入力カード（L882-L984）を **2枚** に分割する。
- **Card 1** (STEP 1): URL入力 + 競合URL + 分析ボタン
- **Card 2** (STEP 2): 詳細設定（expansion廃止して直接表示）+ 進捗

既存の results_container / report_container カードは変更なし（STEP 3として使う）。

---

### Edit P2-A: Card 1 ヘッダーを STEP 1バッジ付きに変更

**場所**: L882-L886

**変更前**:
```python
        with ui.card().classes("card p-6 w-full"):

            ui.label("分析起点").classes("card-title")

            ui.label("URLを入力して「分析を開始」を押すだけで、SEO/AIO分析から改善レポートまで一気通貫で実行します。").classes("card-sub")
```

**変更後**:
```python
        with ui.card().classes("card p-6 w-full step-card-1"):

            with ui.row().classes("items-center gap-2 mb-1"):
                ui.label("STEP 1").classes("text-xs font-bold bg-gray-100 text-gray-500 px-2 py-0.5 rounded tracking-widest")
                ui.label("URL入力").classes("card-title m-0")

            ui.label("URLを入力して「分析を開始」を押すだけで、SEO/AIO分析から改善レポートまで一気通貫で実行します。").classes("card-sub")
```

**ポイント**:
- `with ui.card().classes("card p-6 w-full"):` → `step-card-1` を追加
- `ui.label("分析起点").classes("card-title")` をSTEPバッジ付きの行に変更

---

### Edit P2-B: Card 1 を competitor_input の直後で閉じ、Card 2 を開始

**場所**: L892-L896（competitor_input 〜 expansion の間）

**変更前**:
```python
            competitor_input = ui.input("競合URL（任意）", placeholder="https://competitor.example.com").classes("w-full")

            ui.label("競合比較は自動判定で解析します。").classes("card-hint")

            with ui.expansion("詳細設定（任意・自動判定）", icon="tune").classes("w-full"):
```

**変更後**:
```python
            competitor_input = ui.input("競合URL（任意）", placeholder="https://competitor.example.com").classes("w-full")

            ui.label("競合比較は自動判定で解析します。").classes("card-hint")

        with ui.card().classes("card p-6 w-full step-card-2"):

            with ui.row().classes("items-center gap-2 mb-3"):
                ui.label("STEP 2").classes("text-xs font-bold bg-gray-100 text-gray-500 px-2 py-0.5 rounded tracking-widest")
                ui.label("詳細設定").classes("card-title m-0")

            if True:
```

**ポイント**:
- `ui.label("競合比較は...").classes("card-hint")` の後に Card 1 の `with` が終わる（インデントを8スペースに戻す）
- `with ui.card().classes("card p-6 w-full step-card-2"):` を8スペースで開始 → Card 2 が始まる
- `with ui.expansion(...)` を削除し、代わりに `if True:` ブロックで既存の設定内容を囲む（設定を常時表示に変更）
- expansion内の既存コード（industry_select～balance_slider）はインデントを変えずにそのまま維持

**重要**: `with ui.expansion(...)` の1行だけを `if True:` に置き換える。その中の内容（L899-L936）のインデントは変えない。

---

### Edit P2-C: expansion の終端「閉じカッコ」処理

`with ui.expansion(...):` ブロックを `if True:` に置き換えたことで、
expansion が閉じる部分（balance_slider の後）が `if True:` の終端になる。
これはインデントで自動的に処理されるため、追加の変更は不要。

---

### Edit P2-D: results_container に STEP 3 クラスとバッジを追加

**場所**: L986, L994

**変更前（L986）**:
```python
        results_container = ui.card().classes("card p-6 w-full results-container")
```

**変更後（L986）**:
```python
        results_container = ui.card().classes("card p-6 w-full results-container step-card-3")
```

**変更前（L994）**:
```python
                ui.label("分析結果").classes("card-title")
```

**変更後（L994）**:
```python
                with ui.row().classes("items-center gap-2 mb-1"):
                    ui.label("STEP 3").classes("text-xs font-bold bg-gray-100 text-gray-500 px-2 py-0.5 rounded tracking-widest")
                    ui.label("分析結果 & 改善レポート").classes("card-title m-0")
```

**ポイント**: L993〜L997の `with ui.row()` ブロックはすでにある。`ui.label("分析結果")` だけを置き換える。

---

## Phase 3: スティッキーSTEPバーを追加（Python + JS）

### Edit P3-A: スティッキーバーのPython要素を nav直後に追加

**場所**: L880〜L882（nav html の後、Card 1 の前）

**変更前**:
```python
        ''', sanitize=HTML_SANITIZER.sanitize)

        with ui.card().classes("card p-6 w-full step-card-1"):
```

**変更後**:
```python
        ''', sanitize=HTML_SANITIZER.sanitize)

        with ui.row().classes("step-track w-full"):
            sticky_step1 = ui.label("① URL入力").classes("step-track-item step-track-active sticky-s1")
            ui.label("→").style("color: #D1D5DB; font-size: 14px; line-height: 1;")
            sticky_step2 = ui.label("② 詳細設定").classes("step-track-item step-track-pending sticky-s2")
            ui.label("→").style("color: #D1D5DB; font-size: 14px; line-height: 1;")
            sticky_step3 = ui.label("③ 分析結果").classes("step-track-item step-track-pending sticky-s3")

        with ui.card().classes("card p-6 w-full step-card-1"):
```

**ポイント**: インデントは8スペース（`with ui.column().classes("app-shell"):` の直下）。

---

### Edit P3-B: JavaScriptをHTMLヘッド（`shared=True`のブロック）に追加

**場所**: L856〜L860（`ui.add_head_html("""...""", shared=True)` の文字列末尾）

現在のHTMLブロックの末尾（`""", shared=True,`の手前）に追記する。

**追加するJSコード**（`</style>` と `"""` の間に挿入）:

```html
    <script>
    (function(){
      var ALL = ['step-track-active','step-track-done','step-track-pending'];
      var STEPS = [
        {sel:'.sticky-s1', lbl:'① URL入力',    done:'✓ URL入力'},
        {sel:'.sticky-s2', lbl:'② 詳細設定',  done:'✓ 詳細設定'},
        {sel:'.sticky-s3', lbl:'③ 分析結果',  done:'✓ 分析結果'},
      ];
      var scrollStep = 0;
      var STICKY_H = 76;

      function refreshBar() {
        STEPS.forEach(function(s, i) {
          var el = document.querySelector(s.sel);
          if (!el) return;
          if (el.classList.contains('step-track-done')) return;
          el.classList.remove('step-track-active', 'step-track-pending');
          el.classList.add(i === scrollStep ? 'step-track-active' : 'step-track-pending');
          el.textContent = s.lbl;
        });
      }

      var cards = [];

      function calcScrollStep() {
        var newActive = 0;
        for (var i = 0; i < cards.length - 1; i++) {
          if (!cards[i]) continue;
          var bottom = cards[i].getBoundingClientRect().bottom;
          if (bottom <= STICKY_H + 8) { newActive = i + 1; }
        }
        if (newActive !== scrollStep) {
          scrollStep = newActive;
          refreshBar();
        }
      }

      function initScrollSpy() {
        var sels = ['.step-card-1', '.step-card-2', '.step-card-3'];
        cards = sels.map(function(s){ return document.querySelector(s); });
        if (cards.some(function(c){ return !c; })) {
          setTimeout(initScrollSpy, 250);
          return;
        }
        window.addEventListener('scroll', calcScrollStep, { passive: true });
        calcScrollStep();
        refreshBar();
      }

      setTimeout(initScrollSpy, 450);
    })();
    </script>
```

**挿入場所の特定**:

L854-L860 現在:
```python
    </style>

    """,

    shared=True,

)
```

変更後:
```python
    </style>

    <script>
    (function(){
      ... (上記JSコード) ...
    })();
    </script>

    """,

    shared=True,

)
```

---

## Phase 4: Python動的状態管理（STEPバーのdone/active切替）

分析完了時に STEP 1・2 を「グリーン（done）」、STEP 3 をオレンジに変える。
notecode と同じパターンで **タイマー（1秒周期）+ sync関数** を使う。

### Edit P4-A: ヘルパー定数と関数の追加

**場所**: `main_page()` 関数の中、`sticky_step1/2/3` を宣言したコード（P3-A）の直後に追加。

具体的には、P3-Aで追加した `sticky_step3 = ...` の行の直後（Card 1 の `with` 文の前）に挿入する。

**追加するコード**（インデント8スペース）:

```python
        _STICKY_NOT_DONE = "step-track-active step-track-pending"

        def _mark_sticky_done(badge, text: str) -> None:
            badge.classes(remove=_STICKY_NOT_DONE, add="step-track-done")
            badge.text = text
            badge.update()

        def _unmark_sticky_done(badge) -> None:
            badge.classes(remove="step-track-done")
            badge.update()

        def _refresh_step_indicators() -> None:
            has_result = results_container.visible
            is_busy    = getattr(state, "busy", False)
            url_filled = bool((url_input.value or "").strip())
            if has_result:
                _mark_sticky_done(sticky_step1, "✓ URL入力")
                _mark_sticky_done(sticky_step2, "✓ 詳細設定")
                _unmark_sticky_done(sticky_step3)
            elif is_busy or url_filled:
                _mark_sticky_done(sticky_step1, "✓ URL入力")
                _unmark_sticky_done(sticky_step2)
                _unmark_sticky_done(sticky_step3)
            else:
                _unmark_sticky_done(sticky_step1)
                _unmark_sticky_done(sticky_step2)
                _unmark_sticky_done(sticky_step3)

        step_indicator_timer = ui.timer(1.0, _refresh_step_indicators)
        ui.context.client.on_disconnect(lambda: step_indicator_timer.cancel())
```

**注意点**:
- `url_input` / `sticky_step1` / `sticky_step2` / `sticky_step3` / `results_container` / `state` は同じ `main_page()` スコープで定義済みのため参照可能
- `_refresh_step_indicators` は **sync def**（`async def` にしない）。NiceGUIのタイマーコールバックをasyncにするとcontextエラーが出る

---

## 検証手順

各フェーズ完了後に以下を実行:

```bash
cd C:\tetie\aio2-main
.\.venv\Scripts\python.exe -m py_compile nicegui_app.py
# エラーなし → ブラウザで http://localhost:8081 を開いて目視確認
```

目視確認チェックリスト:
- [ ] P1完了: ブラウザのDevToolsで `.step-track-active` のCSSが存在する
- [ ] P2完了: 3枚のカードが縦に並んでいる（STEP 1/2/3 バッジ付き）
- [ ] P3完了: スクロールするとSTEPバーがナビ下に固定される。Card 2 が画面外に消えると③がアクティブになる
- [ ] P4完了: URLを入力すると①がグリーン。分析完了後に①②がグリーン・③がオレンジ

---

## 変更規模サマリー

| Phase | 編集数 | 変更行数（目安） |
|-------|-------|----------------|
| P1 CSS追加 | 1箇所 | +35行 |
| P2 カード分割 | 4箇所 | +20行, -3行 |
| P3 スティッキーバー（Python + JS） | 2箇所 | +60行 |
| P4 Pythonタイマー | 1箇所 | +30行 |
| **合計** | **8箇所** | **約+145行** |

アルゴリズム変更なし。分析ロジック・結果表示ロジックは一切変更しない。

---

## 既知の制約・注意事項

1. **`ui.expansion` の廃止**: P2-BでexpansionをCard 2直接表示に変えるため、「詳細設定」が常時展開される。折りたたみが必要な場合は `if True:` を `with ui.expansion(...):` に戻す。

2. **JSのStickyH値（76px）**: `--nav-height: 40px` + step-track（約36px）= 76px。step-track の高さが変わった場合はJSの `STICKY_H` を更新する。

3. **`_refresh_step_indicators` のスコープ**: `url_input` はP4-Aより後（Card 1内）で定義されるため、Pythonの定義順に注意。Pythonは関数定義時でなく**呼び出し時**に変数を解決するためクロージャとして問題ない。

4. **`results_container.visible` の参照**: `_refresh_step_indicators` 内で `results_container.visible` を参照しているが、NiceGUIの `.visible` プロパティはPythonオブジェクト側で管理されているため同期的に読める。
