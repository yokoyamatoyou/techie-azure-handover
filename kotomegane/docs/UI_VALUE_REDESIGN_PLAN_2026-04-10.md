# Kotomegane UI Value Redesign Plan 2026-04-10

## Purpose

この文書は、`kotomegane` の UI を

- `何を取得したか`
- `そのデータは何を意味するか`
- `次に何を直すべきか`

が 1 画面で分かる状態へ寄せるための変更計画です。

現状の主問題は、分析後に URL やスコアは並ぶが、ユーザーから見ると

- その URL が `自社 / 競合 / 外部 / 引用候補`
- `実際に引用された` のか `見つかっただけ` なのか
- 結果として `何が良くて / 何が悪いか`

が即読できないことです。

## Fixed Product Decision

- `コトメガネ` は `観測ツール` に徹する
- `アルゴリズムの中身` は主画面で見せない
- ただし `判定の意味` と `根拠の意味` は見せる
- ユーザーに見せるのは `処理方法` ではなく `判断材料`
- URL は生で並べず、`意味ラベル付きの証拠` として見せる
- 主画面は `結論 -> 根拠 -> 次アクション` に固定する

## Current Problem Definition

### 1. URL の意味が分からない

- URL が並んでも、`競合URL` なのか `外部メディア` なのか `自社ページ` なのか分からない
- `回答で使われた引用` と `検索候補に出ただけ` の差が読めない
- URL が多いほど良いのか悪いのか分からない

### 2. 取得処理が前に出すぎる

- `内部質問`
- `反復`
- `cache`
- `何件確認中`

は運用者には必要でも、初見ユーザーの主画面には不要

### 3. 価値の翻訳が足りない

- 現状 UI は `観測した`
- だがユーザーが知りたいのは `AI は誰を薦めたか`
- さらに知りたいのは `なぜそうなったか`
- 最後に欲しいのは `何を直せば変わるか`

### 4. 主画面の情報優先順位が弱い

- KPI や詳細導線がまだ早い段階で目に入る
- 単発確認の結論と定点トレンドの区別が初見で分かりにくい

## External Reference Principles

2026-04-10 時点の公式サイト / 公式ドキュメントを確認した。

### Otterly

参考:
- [Features](https://otterly.ai/features/)
- [Search Prompt Monitoring](https://help.otterly.ai/search-prompt-monitoring)
- [Why analyze citation links](https://help.otterly.ai/analyze-citation-links)

学ぶ点:
- `brand visibility`
- `website citations`
- `prompt monitoring`
- `domain ranking`

を最初から価値として見せている。  
特に `どのページが cited されたか` が主役。

### Peec AI

参考:
- [Docs home](https://docs.peec.ai/)
- [Understanding sources](https://docs.peec.ai/understanding-sources)
- [Adding tracked brands](https://docs.peec.ai/adding-brands)

学ぶ点:
- `sources` と `citations` を明確に分ける
- `brand mentioned` と `source cited` のズレを価値に変える
- `competitors using the same visibility metrics` を自然に扱う

### AthenaHQ

参考:
- [AthenaHQ](https://athenahq.ai/)

学ぶ点:
- `Executive AI Visibility Dashboard`
- `Citation source analysis`
- `prescriptive recommendations`

を 1 つの流れとして見せている。  
単なる可視化ではなく、`経営判断に使える見せ方` に寄せている。

### Scrunch

参考:
- [Understanding the Citations Tab](https://helpcenter.scrunchai.com/en/articles/11944877-understanding-the-citations-tab-in-scrunch)
- [Product update](https://helpcenter.scrunchai.com/en/articles/12333561-mid-september-2025-product-update)

学ぶ点:
- Citation row ごとの意味を明示する
- `brand presence`
- `citation rate`
- `competitor`

の軸で、URL 一覧を `分析可能な表` に変えている。

## Redesign Direction

## 1. Main Screen Must Answer 3 Questions

主画面は次の 3 問だけに答える。

1. AI は今回、自社を薦めたか
2. その結論の根拠は何か
3. 次にどのページ / 論点を直すべきか

## 2. Hide Mechanism, Show Meaning

主画面で隠すもの:

- 内部質問数
- 短文化の詳細
- cache retention
- reasoning
- 反復方式
- planner 署名

主画面で見せるもの:

- 自社が `引用されたか`
- 競合が `引用されたか`
- 外部メディアが `引用されたか`
- 自社は `見つかったが引用されなかったか`
- どの論点で負けたか

## 3. Evidence First, Raw URL Later

URL は次の順で見せる。

1. `今回の結論`
2. `結論の根拠`
3. `引用URL`
4. `候補に出たが未引用`
5. `判定保留`
6. `生URL一覧`

つまり `URL を直接読む UI` ではなく `証拠カテゴリを読む UI` に変える。

## Data Semantics To Expose

各 URL には少なくとも次の意味ラベルを付ける。

- `自社引用`
- `競合引用`
- `外部引用`
- `自社候補`
- `競合候補`
- `外部候補`
- `判定保留`

各 URL row には少なくとも次を表示する。

- ラベル
- タイトル
- ドメイン
- どの質問で出たか
- 回答で引用された回数
- 自社が出た回での出現か
- 自社が出なかった回での出現か

## New Primary Surfaces

### A. Verdict Card

表示するもの:

- `AIの結論`
- `自社優勢 / 自社あり / 外部優勢 / 未露出`
- `AIがどう答えたか` を 1 文
- `自社が引用された回数`
- `直近 run での露出率`

表示しないもの:

- raw score の由来
- deterministic の計算式

### B. Why Card

表示するもの:

- `なぜそう判定したか`
- `自社引用 X件`
- `競合引用 X件`
- `外部引用 X件`
- `自社は候補に出たが未引用 X件`

ここで初めて URL グループを見せる。

### C. Action Card

表示するもの:

- `次に直すページ`
- `次に補強する論点`
- `なぜそこか`
- `期待される変化`

例:

- `比較ページ不足`
- `料金根拠不足`
- `FAQ不足`
- `地域LP不足`
- `第三者サイトばかり引用`

## New Evidence Views

### 1. Citation Summary Table

列:

- 区分
- ドメイン
- タイトル
- 引用回数
- 出現質問数
- 自社露出への寄与
- メモ

デフォルト並び:

1. 外部引用が多い順
2. 競合引用が多い順
3. 自社引用が多い順

狙い:

- `どこに負けているか`
- `どこを取り返すべきか`

をすぐ読む。

### 2. Mention vs Citation Matrix

2 x 2 の意味マトリクスを出す。

- `引用あり / ブランドあり`
- `引用あり / ブランドなし`
- `引用なし / ブランドあり`
- `引用なし / ブランドなし`

価値:

- `名前は出るが根拠が弱い`
- `根拠にはいるがブランド想起されない`

を見分ける。

### 3. Competitor Comparison Strip

競合語があるときだけ表示する。

表示するもの:

- 自社引用率
- 競合引用率
- 並走率
- 未露出率

主語は `競合分析` ではなく `AIが誰を薦めたか` にする。

## Trend Design Rules

### Keep

- 定点トレンド
- 前回比
- 揺れ幅

### Change

- 単発確認と定点計測を明確に分離する
- 単発確認の直後は `今回の結果は単発確認です。下の推移には含めていません。` を強く明示する
- `観測件数` や `累積検索呼び出し` は主画面から外し、設定または運用へ移す

## UX Rules

### Rule 1

主画面には `内部処理の説明` を置かない。

### Rule 2

主画面の補助文は `判定の意味` に使う。  
`処理方式の説明` には使わない。

### Rule 3

URL 一覧は必ずカテゴリの後に出す。  
生URLを最初に見せない。

### Rule 4

`この結果で分かること` を詳細折りたたみではなく、結果カード内に 1 行で出す。

### Rule 5

`内部質問` は user-facing では `関連論点も含めて確認` 程度に留める。

### Rule 6

アルゴリズムの詳細は隠すが、判定の意味は隠さない。

## Implementation Phases

### Phase 1: Information Architecture Rewrite

対象:
- `app.py`
- `ui/dashboard_views.py`
- `ui/detail_views.py`

実装:
- 主画面を `結論 / 根拠 / 次アクション` に固定
- `累積検索呼び出し`
- `観測件数`
- cache 系表示

を主画面から外す

完了条件:
- 初見ユーザーが 10 秒以内に `何が起きたか` を読める

### Phase 2: Evidence Labeling

対象:
- `analysis_core/source_evidence.py`
- `analysis_lib.py`
- `ui/detail_views.py`

実装:
- URL の分類ラベルを強化
- `自社 / 競合 / 外部`
- `引用 / 候補 / 保留`

の二軸で表示する

完了条件:
- URL row を見た瞬間に意味が分かる

### Phase 3: Verdict Explanation Layer

対象:
- `ui/dashboard_views.py`
- 必要なら `analysis_core/metrics.py`

実装:
- 判定理由の短文を生成
- `なぜ外部優勢か`
- `なぜ自社あり止まりか`

を card 上に固定表示する

完了条件:
- スコアを読まなくても判断理由が分かる

### Phase 4: Citation And Gap Views

対象:
- `ui/detail_views.py`
- `ui/charts.py`

実装:
- citation summary table
- mention vs citation matrix
- competitor comparison strip

を追加する

完了条件:
- `URL が並んでいるだけ` の状態を解消する

### Phase 5: Internal Detail Isolation

対象:
- `app.py`
- `ui/admin_views.py`
- `ui/detail_views.py`

実装:
- cache
- internal query
- run budget
- planner signature
- raw technical fields

を `設定` または `運用者向け詳細` へ退避する

完了条件:
- 一般ユーザーがアルゴリズム詳細を読まずに使える

## Stop Rules

- URL の意味づけなしに新しいグラフだけ追加しない
- 主画面に内部用語を戻さない
- `引用` と `候補` を再び混ぜない
- 競合比較を主役に戻さない

## Success Criteria

- URL の意味を説明なしでも読める
- 主画面で `誰が薦められたか` が分かる
- 主画面で `なぜそうなったか` が分かる
- 主画面で `次に何を直すか` が分かる
- 内部処理を知らなくても利用できる

## File Ownership

- `app.py`
  - 画面導線
- `ui/dashboard_views.py`
  - 主結果カード
- `ui/detail_views.py`
  - 根拠表示
- `analysis_core/source_evidence.py`
  - URL 意味分類
- `analysis_core/metrics.py`
  - 判定説明と集約値

## Read With This Plan

- `AGENTS.md`
- `WORKLOG.md`
- `ALGORITHM.md`
- `docs/CURRENT_STATE_2026-03-30.md`
- `docs/DOC_STATUS.md`
- `docs/SAAS_IMPLEMENTATION_PLAN_2026-04-03.md`
- `docs/DESIGN_IMPLEMENTATION_PLAN_2026-04-01.md`
