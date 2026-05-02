# Phase 02: メイン分析エラーUI + 空状態改善

優先度: 🔴 高
状態: ✅ 完了

---

## 背景・問題

現状、競合URL取得エラーは表示されるが、**メイン分析（入力URL）が失敗した場合に
ユーザー向けのエラーメッセージが表示されない**。分析が詰まったまま無言で終わる。

また、各タブのデータが空の場合に「データなし」表示がなく、
ユーザーが「分析できていないのか、スコアが0なのか」判断できない。

---

## 修正内容

### 変更1: `nicegui_app.py` — メイン分析のエラー捕捉とUI表示

現状は `try/except` 内でエラーが `logger.error` に流れるだけで UI 更新がない。

```python
# 修正前（nicegui_app.py の分析実行ブロック付近）
except Exception as e:
    logger.error(f"分析エラー: {e}")
    # ← UI 更新なし

# 修正後
except Exception as e:
    logger.error(f"分析エラー: {e}", exc_info=True)
    error_msg = str(e)
    # ネットワーク系エラーは平易な日本語に変換
    if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
        user_msg = "URLへの接続がタイムアウトしました。URLを確認して再試行してください。"
    elif "403" in error_msg or "forbidden" in error_msg.lower():
        user_msg = "このサイトはクロールをブロックしています（403 Forbidden）。"
    elif "404" in error_msg:
        user_msg = "URLが見つかりません（404）。URLを確認してください。"
    else:
        user_msg = f"分析中にエラーが発生しました: {error_msg[:200]}"
    ui.notify(user_msg, type="negative", timeout=10000)
    result_label.set_text(user_msg)   # result_label は既存の結果表示ラベル
```

### 変更2: 各タブ — データなし時の空状態メッセージ

`core/ui/tabs/aio_tab.py`, `seo_tab.py`, `health_tab.py` の先頭で
データが空の場合に早期リターン＋メッセージ表示。

```python
# aio_tab.py の render_aio_tab() 先頭付近に追加
if not aio_results or not aio_results.get("total_score"):
    ui.label("AIO分析データがありません。分析を実行してください。").classes("card-hint text-gray-400")
    return
```

### 変更3: `nicegui_app.py` — ローディング終了時の確実なUI復元

現状、例外発生時に progress_bar や loading スピナーが表示されたままになる可能性がある。

```python
# finally ブロックで確実に復元
finally:
    loading.visible = False
    progress_bar.visible = False
    analyze_button.enable()
```

---

## 対象ファイル

| ファイル | 変更箇所 |
|---------|---------|
| `nicegui_app.py` | 分析実行ブロックの `except` 節 + `finally` 節（L1360付近） |
| `core/ui/tabs/aio_tab.py` | `render_aio_tab()` 先頭のデータ存在チェック |
| `core/ui/tabs/seo_tab.py` | `render_seo_tab()` 先頭のデータ存在チェック（同様） |
| `core/ui/tabs/health_tab.py` | `render_health_tab()` 先頭のデータ存在チェック（同様） |

---

## 完了条件

- [ ] 存在しないURLを入力したとき「URLが見つかりません」が画面に表示される
- [ ] タイムアウトURLを入力したとき「接続タイムアウト」が画面に表示される
- [ ] エラー後もローディングスピナーが消え、分析ボタンが再び押せる
- [ ] データなしの場合に各タブで「データがありません」が表示される
- [ ] `py_compile` エラーなし
- [ ] WORKLOG.md 更新

---

## 注意事項

- `ui.notify()` は NiceGUI の組み込みトースト通知（画面右下に表示）。`type="negative"` で赤表示。
- エラーメッセージにスタックトレースをユーザーに見せない（セキュリティ上）。`logger.error(..., exc_info=True)` でログには残す。
- `result_label` の変数名は実際のコードで確認すること。`nicegui_app.py` で検索する。
