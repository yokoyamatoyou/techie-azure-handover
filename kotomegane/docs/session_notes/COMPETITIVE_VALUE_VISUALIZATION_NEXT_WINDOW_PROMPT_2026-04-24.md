# Competitive Value Visualization Next Window Prompt 2026-04-24

## Prompt

`C:\tetie\kotomegane` で作業してください。

まず次を順に読んで、現行ルールを確認してください。

1. `AGENTS.md`
2. `WORKLOG.md`
3. `ALGORITHM.md`
4. `docs/CURRENT_STATE_2026-03-30.md`
5. `docs/DOC_STATUS.md`
6. `docs/COMPETITIVE_VALUE_VISUALIZATION_PLAN_2026-04-24.md`
7. `docs/RESULT_UX_IMPLEMENTATION_PLAN_2026-04-14.md`
8. `docs/UI_REDUCTION_IMPLEMENTATION_PLAN_2026-04-14.md`
9. `README.md`

今回の目的は、`コトメガネ` の既存アルゴリズムや保存スキーマを変えず、他社 LLMO / AEO ツールに近い分かりやすさを UI の見せ方だけで追加することです。

## Fixed Constraints

- `C:\tetie\kotomegane`、`C:\tetie\notecode`、`C:\tetie\aio2-main` の共通ヘッダは変更しない
- `ui/styles.py` の `render_top_nav()`、`.top-shell`、`.nav-link`、`.top-logo-*` は原則触らない
- 共通色は現行の `#2F241D`、`#D96B1F`、`#B95416`、クリーム背景を維持する
- 新しい LLM 呼び出し、prompt、query planner、スコアリング、DB schema は追加しない
- 既存の `keyword_result`、`source_url`、`run_session`、query rollup、topic signal、citation evidence だけを使う
- 手動スポット確認の結果は定期分析 KPI の母数へ混ぜない
- 実 URL の長文羅列を first view に戻さない
- user-facing UI に `deterministic_score`、`query_plan`、`batch` などの内部語を出さない

## Implementation Target

`docs/COMPETITIVE_VALUE_VISUALIZATION_PLAN_2026-04-24.md` の Phase 1 から Phase 4 を、小さく実装してください。

優先順:

1. `競合スナップショット`
2. `負け質問ミニヒートマップ`
3. `引用元影響ランキング`
4. `次の改善 strip`

## Expected UI Shape

### First View

既存の `今回の結果` 3 カードは維持します。

追加する場合は 1 行の compact strip に限定し、first view に新しい大きなカードを増やさないでください。

表示例:

- `AIが先に見ている相手`
- `自社`
- `比較対象`
- `外部サイト`
- `今回は外部寄り / 自社優位 / 比較対象と混在`

### Detail / Tabs

`今回だけの整理` または `結果詳細` の冒頭に、最大 5 行の `負け質問ミニヒートマップ` を入れてください。

`実URLと参照元を詳しく見る` または `結果詳細` 内に、`回答に効いた根拠サイト Top 5` を入れてください。

`次に足す論点` は文章を増やすのではなく、既存 `Page Opportunity Strip` 系の短い strip 表示へ寄せてください。

## Suggested File Ownership

- `ui/result_story_builders.py`
  - 既存データから view-model を作る
  - 新しい scoring や判定アルゴリズムは作らない
- `ui/result_cards.py`
  - first view の compact rendering
- `ui/detail_views.py`
  - detail 側の mini heatmap / source influence ranking
- `ui/styles.py`
  - body 側の strip / mini heatmap / ranking 用 class を追加
  - common header class は変更しない
- `app.py`
  - 配置と wiring のみ

## Copy Rules

使ってよい文言:

- `AIが先に見ている相手`
- `自社 / 比較対象 / 外部サイト`
- `負けている質問`
- `回答に効いた根拠サイト`
- `次に足す論点`
- `手動スポット確認は参考表示`

避ける文言:

- `競合に負けた` の強い断定
- `AIが評価した理由` のような、根拠以上に踏み込む表現
- `batch`
- `deterministic_score`
- `query_plan`

## UI Traversal Verification

実装後は、次の 3 段階で確認してください。

### Level 1: Static / Import

必須:

```powershell
.\.venv\Scripts\python.exe -m py_compile app.py ui\result_cards.py ui\result_story_builders.py ui\detail_views.py ui\charts.py ui\styles.py
.\.venv\Scripts\python.exe -c "import app; print('IMPORT_OK')"
```

### Level 2: API Key 不要の UI 走査

目的:

- 共通ヘッダが崩れていない
- first view の認知負荷が増えていない
- 保存済み DB 由来の累積結果、タブ、詳細、追加した可視化が描画される

確認手順:

1. `.\run.ps1` で `http://127.0.0.1:8083/` を起動する
2. headless browser / Playwright 互換のスクリプトで `/` を開く
3. 次の文字列または要素を確認する
   - `TECHIE HUB`
   - `見え方観測`
   - `1回だけ分析`
   - `今回の結果`
   - `観測の推移`
   - 追加した `AIが先に見ている相手`
   - 追加した `負けている質問` または `回答に効いた根拠サイト`
4. desktop と mobile の screenshot を `logs/` に保存する

注意:

- この Level 2 は API を叩かない
- `今回の結果` が session-scoped で空の場合でも、保存済み累積側と detail 側の描画確認は行う
- 既存 DB に表示できる保存済み結果がない場合は、UI 骨格と空状態の崩れだけを確認する

### Level 3: Live Output Smoke

目的:

- `1回だけ分析` を押し、実際の provider 応答から `今回の結果` まで出ることを確認する

実施条件:

- `.env` または環境変数に `OPENAI_API_KEY` がある
- 少額の API コスト発生を許容できる
- live smoke 用に確認回数を最小化する。ただし本番設定を壊さない

確認手順:

1. UI で短い質問、自社 URL、任意の名称を入力する
2. `1回だけ分析` を押す
3. `分析中` の progress copy が出ることを確認する
4. 完了後に `今回の結果` 3 カードが出ることを確認する
5. 追加した `競合スナップショット`、`負け質問ミニヒートマップ`、`引用元影響ランキング` のうち、データがあるものが表示されることを確認する
6. screenshot と簡単な JSON / text log を `logs/competitive_value_ui_smoke_YYYY-MM-DD.*` に保存する

注意:

- API key がない場合、Level 3 は未実施でよい。未実施理由を final に明記する
- live smoke のために設定ファイルを一時変更した場合は、必ず元に戻す
- 定期分析 KPI に手動スポット確認が混ざっていないことを確認する

## Completion Conditions

- 共通ヘッダが変わっていない
- 新しいアルゴリズム、LLM 呼び出し、DB schema が増えていない
- first view の読み量が増えすぎていない
- `自社 / 比較対象 / 外部サイト` の位置関係が一目で分かる
- `どの質問が弱いか` が最大 5 行で見える
- `どの根拠サイトが効いたか` が URL 羅列ではなくランキングで読める
- `py_compile` と `import app` が通る
- Level 2 の UI 走査を実施する
- API key とコスト許容がある場合のみ Level 3 live output smoke を実施する

## Final Report Format

最後に次を簡潔に報告してください。

- 変更した主な UI
- 触ったファイル
- 共通ヘッダを変更していないこと
- 実施した検証
- Level 3 live output smoke を実施したか、未実施なら理由

## Current Completion Report 2026-04-24

このセクションは、2026-04-24 の実装後に別ウインドウへ引き継ぐための現況です。

### Implemented

- `ui/result_cards.py`
  - first view の `今回の結論` カード内に `AIが先に見ている相手` の compact snapshot を追加
  - 自社 / 比較対象 / 外部サイトの引用・候補バランスを share bar と chip で表示
  - `頻出論点` カード内に `次の改善 strip` を追加
- `ui/detail_views.py`
  - `結果詳細` 内に `負けている質問` のミニヒートマップを追加
  - `根拠URLの状態` 内に `回答に効いた根拠サイト` ranking を追加
- `ui/result_story_builders.py`
  - `build_competitive_snapshot_summary`
  - `build_source_influence_rows`
  - `build_losing_prompt_heatmap_rows`
  - 既存の citation / evidence / prompt family / page gap 集計を UI 用に整形するだけで、新しい LLM 呼び出しやスコアリングは追加していない
- `ui/styles.py`
  - `.competitive-snapshot*`
  - `.competitive-sharebar*`
  - `.mini-heatmap*`
  - body 側の追加 UI class のみ追加
- docs
  - `docs/COMPETITIVE_VALUE_VISUALIZATION_PLAN_2026-04-24.md`
  - `docs/DOC_STATUS.md`
  - `docs/CURRENT_STATE_2026-03-30.md`
  - `README.md`
  - `WORKLOG.md`

### Preserved

- `ui/styles.py` の `render_top_nav()`
- `.top-shell`
- `.nav-link`
- `.top-logo-*`
- `kotomegane` / `notecode` / `aio2-main` の共通ヘッダ方針
- 既存 DB schema
- 既存 prompt / query planner / LLM 呼び出し
- 定期分析 KPI の母数。手動スポット確認を定期 KPI に混ぜる変更はしていない

### Verified

実行済み:

```powershell
.\.venv\Scripts\python.exe -m py_compile app.py ui\result_cards.py ui\result_story_builders.py ui\detail_views.py ui\charts.py ui\styles.py
.\.venv\Scripts\python.exe -c "import app; print('IMPORT_OK')"
.\.venv\Scripts\python.exe -m unittest tests.test_security_hardening
```

合成 rows / evidence による view-model smoke も実施済み。

確認できた出力:

- `SNAPSHOT_HEADLINE: 根拠が複数の相手に分かれています`
- `SOURCE_RANKING: ['導入事例', 'LLMO比較ランキング']`
- `LOSING_HEATMAP: ...`
- `PAGE_STRIP: [('比較ページ', '次に足す')]`
- `VIEW_MODEL_SMOKE_OK`

Playwright headless で `http://127.0.0.1:8083/` の shell 表示も確認済み。

確認できた shell 文言:

- `TECHIE HUB`
- `コトメガネ`
- `見え方観測`
- `今回の結果`
- `観測の推移`

### Not Yet Verified

- 起動済みプロセスでは `今回の結果` が session-scoped empty state だったため、追加した結果内ブロックの実 DOM 表示は未確認
- Level 3 live output smoke は未実施。理由は API 実行コストが発生するため
- 次ウインドウで確認する場合は、既存の saved result を current result として復元できる条件を作るか、API key / コスト許容のうえで短い live run を実施する

### Next Window Recommended Task

1. まず `WORKLOG.md` の `2026-04-24 Competitive Value Visualization Plan` を読む
2. `py_compile` と `import app` を再実行する
3. app を再起動して、編集後コードが 8083 に反映されていることを確認する
4. 既存保存結果または live run で `今回の結果` を表示する
5. 次の文言が DOM に出るか確認する
   - `AIが先に見ている相手`
   - `負けている質問`
   - `回答に効いた根拠サイト`
6. desktop / mobile の screenshot を `logs/competitive_value_ui_smoke_2026-04-24_*` に保存する
7. API key / コスト許容がない場合、Level 3 は未実施として明記する
