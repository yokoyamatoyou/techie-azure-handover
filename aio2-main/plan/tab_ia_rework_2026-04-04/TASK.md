# tab_ia_rework_2026-04-04 TASK

このファイルは、別タブで実装するときの phase / owner / done condition を固定する。

## Global Rules

- 分析ロジック、スコア式、判定意味は変えない
- `C:\tetie\zip` は mock として参照のみ。変更しない
- 1 phase ごとに live / saved の両方を確認する
- 同一情報を 2 タブへ置かない
- `公式条件` と `内部ヒューリスティック` と `任意メモ` を混ぜない
- `FAQ本文` と `FAQPage 実装` を混ぜない
- 途中切れの表示を前提にしない

## Shared Check Commands

### Compile Gate

```text
C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\panels.py core\ui\dashboard.py core\ui\tabs\aio_tab.py core\ui\tabs\health_tab.py core\application\analysis_run_service.py
```

### Targeted Regression Gate

```text
C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_analysis_run_service.py tests\test_characterization_ui.py tests\test_executive_summary.py
```

## Phase Map

### Phase 0: baseline inventory 固定

- Objective:
  - 現行 live / saved の表示要素を棚卸しし、削除対象と残す対象を確定する
- Owner:
  - `core/ui/panels.py`
  - `core/ui/dashboard.py`
  - `core/ui/tabs/aio_tab.py`
  - `core/ui/tabs/health_tab.py`
- DoD:
  - `現状 -> 新タブ` マッピング表を更新済み
  - FAQ / llms / provider の owner タブが確定している

### Phase 1: snapshot data contract 拡張

- Objective:
  - saved workspace が薄くならない保存粒度へ拡張する
- Owner:
  - `core/application/analysis_run_service.py`
- Required work:
  - `summary_workspace` 追加
  - `task_workspace` 追加
  - `writing_workspace` 追加
  - `implementation_workspace` 追加
  - `comparison_workspace` 追加
  - provider full payload 保存
  - faq detection / faq suggestions 保存
  - schema / platform guidance 保存
- DoD:
  - result JSON なしでも snapshot だけで主要タブが再表示できる

### Phase 2: live workspace 上位タブ再編

- Objective:
  - live 画面を `サマリー / やること / 文章改善 / 実装・設定 / 履歴と比較` に差し替える
- Owner:
  - `core/ui/panels.py`
- Required work:
  - `現状 / 改善方法 / 詳細 / 内部診断` を廃止
  - nested detail tabs を廃止
  - 5 タブ構成へ統合
- DoD:
  - live 画面で nested tabs が残っていない
  - default tab は `サマリー`

### Phase 3: saved workspace parity

- Objective:
  - saved workspace のタブ構成を live と一致させる
- Owner:
  - `core/ui/panels.py`
  - `core/ui/dashboard.py`
- Required work:
  - `概要 / AI認識改善 / SEO改善 / 履歴 / 実装メモ` を新タブへ置換
  - snapshot を新タブ単位で描画
- DoD:
  - live と saved でタブ名が一致
  - user がタブ移動で迷わない

### Phase 4: content relocation

- Objective:
  - 重複と不足を同時に解消する
- Owner:
  - `core/ui/panels.py`
  - `core/ui/tabs/aio_tab.py`
  - `core/ui/tabs/health_tab.py`
- Required work:
  - provider 状態を `実装・設定` のみに集約
  - FAQ 内容は `文章改善`
  - FAQPage / schema / validation は `実装・設定`
  - llms.txt は `実装・設定`
  - generic help text を撤去
- DoD:
  - 同一項目が別タブに再掲されていない
  - `文章改善` と `実装・設定` の境界が明確

### Phase 5: visual compression と progressive disclosure

- Objective:
  - 情報量を落とさず、初期表示の負荷だけ下げる
- Owner:
  - `core/ui/panels.py`
  - `core/ui/dashboard.py`
- Required work:
  - status matrix / chips / before-after card を統一
  - fail / warn を優先開示
  - explanation text を badge / metric / section title に置換
- DoD:
  - 長文の常設説明が消えている
  - 重要情報は視覚要素で判断できる

### Phase 6: verify

- Objective:
  - live / saved / mobile / empty state の regression を抑える
- Owner:
  - UI shell
  - persistence owner
- Required checks:
  - Compile Gate
  - Targeted Regression Gate
  - live manual verify
- Manual verify:
  - FAQあり URL
  - FAQなし URL
  - llms.txt あり URL
  - llms.txt なし URL
  - provider fail を含む URL
  - competitor あり / なし
- DoD:
  - 主要 6 パターンで意味の欠落がない

## Implementation Notes By Tab

### サマリー

- first screen で見せるのは `結論`, `最優先3件`, `要対応件数` まで
- `公開条件の詳細` は出さない

### やること

- action は `area` 別ではなく、`担当` と `優先度` で読ませる
- `AI認識改善` と `SEO改善` の分断をやめる

### 文章改善

- `タイトル`, `説明文`, `本文`, `引用候補`, `FAQ`
- FAQ がなければ、候補 3〜5 件を自動生成

### 実装・設定

- provider matrix
- official / heuristic / informational の 3 層
- robots / noindex / nosnippet / schema / llms / platform guidance

### 履歴と比較

- 前回比と競合比較のみ
- 履歴ログの説明テキストを増やさない

## Stop Conditions

- 新タブ名と実際の内容が再びズレた
- snapshot を増やさず UI だけで解決しようとしている
- `llms.txt` を hard requirement として表示し始めた
- FAQ を generic help として戻してしまった
