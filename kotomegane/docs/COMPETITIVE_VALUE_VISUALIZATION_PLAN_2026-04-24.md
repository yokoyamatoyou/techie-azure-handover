# Competitive Value Visualization Plan 2026-04-24

## Purpose

`コトメガネ` の既存アルゴリズムと保存データを変えず、見せ方だけで他社 LLMO / AEO ツールに近い分かりやすさと付加価値を出す。

今回の対象は、ユーザーが 5 秒以内に次を読める状態へ寄せること。

1. AI は自社、比較対象、外部のどれを見ているか
2. どの質問で負けているか
3. どの根拠サイトやページが回答に効いているか
4. 次にどのページ・論点を直せばよいか

## Fixed Constraints

- `C:\tetie\kotomegane`、`C:\tetie\notecode`、`C:\tetie\aio2-main` の共通ヘッダは変更しない
- `ui/styles.py` の `render_top_nav()`、`.top-shell`、`.nav-link`、`.top-logo-*` は原則触らない
- 共通トークンは現行の `#2F241D`、`#D96B1F`、`#B95416`、クリーム背景を維持する
- 新しい LLM 呼び出し、prompt、query planner、スコアリング、DB schema は追加しない
- 既存の `keyword_result`、`source_url`、`run_session`、query rollup、topic signal、citation evidence だけを使う
- 手動スポット確認の結果は自動定期分析の母数へ混ぜない
- 手動で取った外部情報を数値グラフに直接混ぜない。現時点では既存 `manual` run を点線・薄色の参考系列として見せる範囲に留める

## Current Gap

現状は `今回の結論 / 根拠に使われたサイト / 頻出論点` まで整理済みだが、競合ツールが強く見せている次の価値が弱い。

- `自社 vs 比較対象 vs 外部` の勝ち負けが first view で見えにくい
- 「どの質問で負けたか」が下段の詳細に寄り、初見で価値を感じにくい
- 引用元 URL は整理されているが、「どの引用元が回答を動かしたか」のランキング感が弱い
- 論点 chip はあるが、競合差分や改善優先度として読ませきれていない

## Design Direction

### One Fold, One Judgment

first view は説明を増やさず、現在の 3 カード構成を維持する。追加する情報は 1 つの compact summary strip にまとめ、ヘッダや入力導線より強くしない。

### Use Shape Before Text

文章説明より、横棒、3 分割バー、ヒートマップ、短いランキングで読む。補助文は 1 ブロック 1 行から 2 行までに制限する。

### Keep Detail Below

実 URL、件数、raw answer、詳しい質問タイプ別内訳は `結果詳細` と `定期分析の推移` に残す。first view では結論だけを見せる。

## Recommended Release Scope

### Phase 1: Competitive Snapshot Strip

目的:

- `AI が誰を先に見ているか` を first view で即読みにする。

表示:

- `自社`
- `比較対象`
- `外部サイト`

の 3 区分を横並びの share bar で表示する。

データ:

- `aggregate_url_evidence(...)`
- `build_evidence_stats(...)`
- `competitor_mentions`
- `target_domain_hit`
- `brand_mention_hit`

実装方針:

- 新規 builder は `ui/result_story_builders.py` に置く
- 描画は `ui/result_cards.py` の `render_latest_result_cards(...)` 内で、既存 3 カード直下か中央カード内の下部へ置く
- 表示は最大 3 区分、数値は `%` ではなく `強い / 並走 / 弱い` の短ラベルを主にする

完了条件:

- first view で `今回は自社優位 / 外部優位 / 比較対象混在` が一目で分かる
- 既存 3 カードの高さが大きく増えない
- card 内の補助文が増えない

### Phase 2: Losing Prompt Mini Heatmap

目的:

- `どの質問で負けたか` を詳細タブへ行く前に見せる。

表示:

- 行: 最大 5 件の質問または質問タイプ
- 列: `自社引用`、`比較対象引用`、`外部引用`
- 色: 既存 semantic color を使う

データ:

- 既存 `build_question_result_heatmap_chart(...)` の考え方を流用
- 新しい判定ロジックは作らず、既存の citation / evidence status を見る

実装方針:

- first view には full plotly ではなく、軽量な HTML / NiceGUI chip matrix として出す
- 詳細版は既存の `定期分析の質問ごとの結果` を維持する
- 追加位置は `結果詳細` の冒頭、または `今回の結果` タブの `今回だけの整理` 内に限定する

完了条件:

- 5 秒レビューで `弱い質問` を 1 つ言える
- mobile で横スクロールを発生させない
- 手動スポット確認と定期分析が混在して見えない

### Phase 3: Source Influence Ranking

目的:

- `どの引用元がAI回答を動かしているか` を URL 羅列ではなくランキングで見せる。

表示:

- `回答に効いた根拠サイト Top 5`
- 各 item は `ページ名 / ドメイン / 自社・比較対象・外部 / 引用登場の強さ`

データ:

- `build_source_focus_summary(...)`
- `aggregate_url_evidence(...)`
- `resolve_citation_records(...)`

実装方針:

- first view では Top 3 のまま
- `結果詳細` に Top 5 の horizontal ranking を追加
- 実 URL は引き続き詳細表に置き、ランキングには raw URL を主表示しない

完了条件:

- `外部記事を取りに行くべきか / 自社ページを補強すべきか` が読みやすい
- URL が長くて画面を圧迫しない

### Phase 4: Action Summary Reframe

目的:

- `次に足す論点` を、競合比較の文脈で読ませる。

表示:

- `今すぐ直す`
- `次に足す`
- `維持`

の 3 状態で、既存 `Page Opportunity Strip` を first view か detail 冒頭へ出す。

データ:

- `build_page_opportunity_strip_rows(...)`
- `build_page_gap_rows(...)`
- `topic_signals["action_topics"]`

実装方針:

- 新しい不足判定は作らない
- 既存の page gap と topic signal を、短いラベルと state color で再表示する
- `改善を実行する` ではなく `改善判断の材料` として表現する

完了条件:

- 右カードが文章だけで埋まらない
- `何を直すか` が 1 画面で分かる

## Manual Data Policy

手動で取得した情報は、現時点では自動観測グラフの数値に混ぜない。

理由:

- 自動観測は `同じ条件で繰り返した回答試行` が母数
- 手動取得は頻度・対象・条件が揃いにくく、同じ折れ線に入れると信頼性が落ちる
- 競合比較の説得力は、母数を壊さないことが重要

採用する見せ方:

- 既存 `manual` run は `手動スポット確認` として薄色・点線・hover label で表示する
- `定期分析の推移` の主 KPI には混ぜない
- 将来の手動メモ入力は別 phase とし、時系列グラフ上の `注釈マーカー` として扱う

## Screen Placement

### First View

維持:

- 共通ヘッダ
- hero
- 入力
- 実行モード
- `今回の結果` 3 カード
- `観測の推移`

追加:

- `今回の結果` 3 カード内または直下に `競合スナップショット` を 1 行だけ追加

避ける:

- 新しい大見出しカードを first view に増やす
- 長い説明文を追加する
- chart を 2 つ以上 first view に増やす

### Detail / Tabs

追加:

- `今回だけの整理` に `負け質問ミニヒートマップ`
- `実URLと参照元を詳しく見る` に `引用元影響ランキング`
- `定期分析の推移` の下段に既存ヒートマップの見出しを `どの質問で負けているか` へ寄せる

## File Ownership

- `ui/result_story_builders.py`
  - 競合スナップショット、引用元ランキング、負け質問 rows の view-model 作成
- `ui/result_cards.py`
  - first view の compact rendering
  - 3 カード内の密度調整
- `ui/charts.py`
  - 既存 heatmap / bar chart の見た目調整
  - 新規アルゴリズムは追加しない
- `ui/styles.py`
  - body card / strip / mini heatmap の visual token 追加
  - `render_top_nav()` と `.top-shell` 系は変更しない
- `app.py`
  - 配置と wiring のみ
  - データ処理は追加しない
- `ui/detail_views.py`
  - detail 側のランキングとミニヒートマップの置き場

## Copy Rules

採用:

- `AIが先に見ている相手`
- `自社 / 比較対象 / 外部サイト`
- `負けている質問`
- `回答に効いた根拠サイト`
- `次に足す論点`
- `手動スポット確認は参考表示`

避ける:

- `競合に負けた` だけの強い断定
- `AIが評価した理由` のような、根拠以上に踏み込む表現
- 内部語 `batch`、`query_plan`、`deterministic_score`
- first view での raw URL 長文表示

## Visual Rules

- `自社`: existing `--self`
- `比較対象`: existing `--competitive`
- `外部`: existing `--external`
- 主 CTA と active state は existing orange-brown を使う
- 新規カードは `section-card` より軽い surface にし、主結果 3 カードより強くしない
- chip は最大 4 個まで
- first view の追加 copy は 2 行以内
- mobile では mini heatmap を縦並びにし、plotly chart は増やさない

## Implementation Order

1. `ui/result_story_builders.py` に既存データだけで作る view-model を追加する
2. `ui/result_cards.py` に `競合スナップショット` の compact component を追加する
3. `ui/styles.py` に `.competitive-snapshot-*`、`.mini-heatmap-*`、`.source-influence-*` を追加する
4. `ui/detail_views.py` または `app.py` の result tab に `負け質問ミニヒートマップ` を配置する
5. `結果詳細` に `引用元影響ランキング` を配置する
6. 既存文言を短縮し、追加分で総文字量が増えないように削る

## Verification

### Static

- `.venv\Scripts\python.exe -m py_compile app.py ui\result_cards.py ui\result_story_builders.py ui\detail_views.py ui\charts.py ui\styles.py`
- `.venv\Scripts\python.exe -c "import app; print('IMPORT_OK')"`

### UI

- `http://127.0.0.1:8083/` が HTTP 200
- desktop screenshot で共通ヘッダの高さ、色、リンク順が変わっていない
- mobile screenshot で first view の縦積みが増えすぎていない
- 5 秒レビューで `誰が見られているか / どの質問が弱いか / 次に何を見るか` を言える

### Regression

- 手動スポット確認が定期分析 KPI に混ざらない
- `今回の結果` が session-scoped のまま維持される
- periodic refresh で結果詳細が勝手に閉じない
- provider / model / prompt / scoring は変更されない

## Non Goals

- 新しい LLM 分析
- prompt volume 推定
- sentiment model の追加
- AI crawler audit
- 手動注釈 DB
- CSV importer
- SaaS 課金・権限制御
- `notecode` / `aio2-main` 側の変更

