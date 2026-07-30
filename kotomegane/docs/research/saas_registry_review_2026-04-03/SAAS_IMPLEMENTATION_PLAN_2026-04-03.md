# Kotomegane SaaS Implementation Plan 2026-04-03

## 0. Purpose

この文書は `kotomegane` を PoC から `企業向けSaaSとして通用する実装` へ寄せるための現行実装計画です。

今回の対象は次です。

1. 評価ロジックを `LLMの自己採点依存` から下げる
2. 反復実行の揺れを見える化する
3. UI を `認知負荷が低い SaaS` に寄せる
4. provider ごとの差を `設定と adapter` に閉じ込める

今回の対象外は次です。

1. 地域別分析
2. 本格 SaaS 化のための tenant 分離、RBAC、監査基盤、課金
3. Windows service や外部 scheduler への移行

上記 2 は、SaaS 化フェーズに入る時点で別計画に分離する。

## 1. Fixed Product Direction

- `kotomegane` は `AI回答で自社が見えるか` を測る可視化 SaaS として扱う
- 主役は `自社露出の測定` と `次に直すページの判断`
- `競合比較` は補助であり、主導線にはしない
- provider 差分は UI に露出しすぎない
- 画面は `入力 -> 結論 -> 深掘り` の 3 段導線を守る
- 主画面に説明文を積みすぎない
- 文字量より `1画面で分かる次行動` を優先する

## 2. UX Guardrails

### 2.1 Nielsen 10 Principles Mapping

1. Visibility of system status
   - 実行中、Batch中、待機中、失敗中を常に 1 箇所で見せる
   - ステータス文は 1 行で短く出す
2. Match between system and real world
   - `visibility score` を前面に出しすぎず、`自社が出た / 出ない / 外部が強い` を主表示にする
   - 内部語は極力出さない
3. User control and freedom
   - `通常実行`
   - `まとめて確認`
   - `定期チェック`
   を明確に分離する
4. Consistency and standards
   - CTA、色、カード階層、表ラベルを TECHIE 共通文法に揃える
5. Error prevention
   - 必須入力不足、provider未実装、予算超過見込みを実行前に止める
6. Recognition rather than recall
   - 設定を覚えさせず、保存済み `確認内容` から再利用させる
7. Flexibility and efficiency of use
   - 初見は 1 質問から
   - 慣れたユーザーは `確認内容 / 定期チェック / まとめて確認` を使う
8. Aesthetic and minimalist design
   - 主画面に表示する主役カードは 3 枚まで
   - 主画面に長文説明を置かない
9. Help users recognize, diagnose, and recover from errors
   - エラーは `何が足りないか / 何を直せば再実行できるか` を短文で返す
10. Help and documentation
   - 画面内ヘルプは短く
   - 詳細手順は docs に逃がす

### 2.2 Hick's Law Rules

- 1ブロック内の主要選択肢は最大 3 個
- 同時に見せる主CTAは最大 2 個
- 初期画面では `分析を実行` を主CTAに固定する
- provider 選択は初期画面では見せず、詳細設定に置く
- 詳細機能はタブか折りたたみへ下げる
- 1カード内の説明文は原則 2 行以内

### 2.3 Text Density Rules

- H1 下の価値訴求は 1 文だけ
- セクション補助文は 40 字前後まで
- KPI カード内は `ラベル / 値 / 補助 1 行` に制限する
- 結果一覧の列は増やしすぎない
- 長文の説明や rationale は detail card に逃がす

## 3. Architecture Direction

### 3.1 Must Keep

- `query_plan` 保存
- `answer_text` と `citations` 保存
- `repeat_count` ベースの反復
- `question_set` / `schedule` / `batch_job` の保存

### 3.2 Must Change

- `visibility_score` の主決定を LLM 自己申告から下げる
- provider ごとの batch / cache / expansion 差分を分離する
- run 比較を `平均だけ` から `揺れも確認` に進める

### 3.3 Billing And Packaging Direction

課金と実行制御は早い段階で module 化する。

最低限、次の責務を分ける。

1. `plan_catalog`
   - プラン名
   - 手動可否
   - batch 可否
   - provider ごとの 1 実行あたり総質問数上限
2. `billing_rules`
   - `service x mode x provider_count` ごとの課金単位
   - 手動クレジットと batch 料金の分離
3. `run_policy`
   - 手動は順次表示
   - batch は全件揃うまで待機し、24時間経過で暫定表示へ切り替える

現時点で固定するルール:

- `コトメイク` 手動: 1回 1クレジット
- `コトミガキ` 手動: 1回 1クレジット
- `コトメガネ` 手動: 1回 2クレジット
- `コトメガネ` batch: 手動クレジットとは別料金
- `コトメガネ` batch 料金単位: batch 作成時点で 1 単位消費

`provider_count` は将来の複数 provider 手動実行に備えて持つが、現時点の既定課金は固定値でもよい。

### 3.4 Provider Strategy

次はハードコーディングしない。

1. Batch 実行方法
2. prompt caching の指定方法
3. query expansion の実行方式
4. provider ごとのサポート可否

代わりに、`provider capability registry` を設ける。

最低限 registry で持つ項目:

- `supports_live_requests`
- `supports_batch`
- `supports_prompt_cache`
- `supports_extended_prompt_cache`
- `supports_query_planner_reuse`
- `preferred_batch_mode`
- `cache_policy_mode`
- `expansion_mode`
- `max_expansion_queries`
- `cost_reduction_note`

方針:

- OpenAI は現状機能を維持する
- Gemini / Claude は `planned` のままでも、差分吸収ポイントだけ先に設計する
- 安くする方法が provider ごとに弱い場合は、`非対応` を registry で明示する
- 安くできない provider に無理な共通実装を強要しない

現行の基本想定モデル:

- OpenAI: `gpt-5.4-nano`
- Gemini: `gemini-3.1-flash-lite-preview`
- Claude: `claude-haiku-4-5`

現行の基本実行数:

- 手動 OpenAI: 合計質問数 30
- 手動 Gemini: 合計質問数 30
- 手動 Claude: 合計質問数 15

上記の合計質問数は、拡張質問込みの総数として扱う。

## 4. Scoring Direction

### 4.1 Target State

`visibility_score` は最終的に rule-based に近づける。

LLM の役割:

- 回答本文の生成
- citation の抽出
- competitor mention の候補抽出
- 短い business summary の生成

アプリ側の役割:

- 自社ドメイン hit 判定
- ブランド hit 判定
- citation domain の正規化
- 競合出現判定
- 回答タイプ分類
- 最終スコア算出
- verdict 算出

### 4.2 New Score Inputs

最終スコアの入力値は次を使う。

1. `owned_domain_hit`
2. `brand_mention_hit`
3. `owned_citation_count`
4. `owned_citation_share`
5. `competitor_mention_hit`
6. `external_only_result`
7. `answer_type_key`
8. `repeat_consistency`

### 4.3 Score Rules

- LLM から返る `visibility_score` は一旦 `raw_llm_score` として保持する
- UI 主表示は `deterministic_score` を使う
- `raw_llm_score` は比較用の参考値に下げる
- `deterministic_score` の算出式は code 内に明示する
- 係数は config から読めるようにする

## 5. Variance And Trust Rules

反復実行の価値は `平均` だけでは足りない。

最低限、各 run で次を持つ。

1. `avg_visibility_score`
2. `median_visibility_score`
3. `min_visibility_score`
4. `max_visibility_score`
5. `score_stddev`
6. `owned_hit_rate`
7. `competitor_hit_rate`
8. `external_lead_rate`

UI では全部を初期表示しない。

主画面では次だけ出す。

- 自社露出率
- 平均スコア
- 揺れ幅が大きいかどうか

`揺れ幅が大きい` の判定は rule-based にする。

例:

- `score_stddev >= threshold`
- `min` と `max` の差が大きい
- `owned_hit_rate` が 50% 未満

## 6. Phase Structure

各 Phase は必ず次の順で進める。

1. 実装
2. 自己テスト
3. 失敗時の自己修正
4. 完了条件判定
5. 次 Phase へ進む

自己修正は 3 回まで。

ルール:

- 1 回目で原因を切り分ける
- 2 回目で局所修正する
- 3 回目で最小安全案に落とす
- 3 回失敗したら、その Phase は停止し、未完として記録する

## 7. Phase Plan

### Phase 0: Preflight

目的:
- 現行ベースラインを固定する

対象ファイル:
- `app.py`
- `analysis_lib.py`
- `llmo_client.py`
- `config.py`
- `storage.py`
- `query_planning.py`

実装手順:
1. 現行 docs と実装の source of truth を確認する
2. 既存の主要画面をスクリーンショットで保存する
3. 現在の実行、Batch、定期チェック導線を開けることを確認する
4. 既存 export が出ることを確認する

自己テスト:
1. `.venv\Scripts\python.exe -m py_compile app.py analysis_lib.py llmo_client.py storage.py config.py query_planning.py`
2. `.venv\Scripts\python.exe -c "import app"`
3. `run.ps1` 起動後に HTTP 200 を確認する

完了条件:
- baseline screenshot が保存済み
- import smoke が通る
- HTTP 200 が返る

### Phase 1: Provider Capability Registry

目的:
- provider ごとの差分を config / adapter 側へ閉じ込める

対象ファイル:
- `config.py`
- `llmo_client.py`
- 必要なら `README.md`

実装手順:
1. provider catalog に capability 項目を追加する
2. OpenAI の現在値を registry に移す
3. Batch 実行可否を registry から判定する
4. prompt cache の扱いを registry 経由にする
5. expansion の扱いを registry で表現できる形へ揃える
6. provider ごとの default model と default total question budget を registry に移す
7. batch timeout と partial display policy を registry に移す

自己テスト:
1. OpenAI で現行 manual run が壊れていない
2. OpenAI で Batch 導線が壊れていない
3. Gemini / Claude は `planned` のまま UI と内部判定が矛盾しない
4. OpenAI 30 / Gemini 30 / Claude 15 の総数設定を取得できる

自己修正上限:
- 3 回

完了条件:
- provider 差分を if 文の散在ではなく registry から読める
- OpenAI 現行機能が維持される

### Phase 2: Query Planning And Cache Strategy Refactor

目的:
- 拡張質問、prompt caching、Batch 順序の責務を分離する

対象ファイル:
- `query_planning.py`
- `app.py`
- `llmo_client.py`
- `config.py`

実装手順:
1. query expansion の設定値を config 化する
2. provider ごとの expansion 制限値を参照できるようにする
3. prompt caching を効かせる送信順序を関数に切り出す
4. Batch と通常実行で同じ execution plan を使える状態にする
5. hard-coded な query suffix 群は `template set` として分離する
6. `拡張質問込みの合計質問数` を超えないよう planner 側で enforce する

自己テスト:
1. 同じ元質問で `query_plan` 再利用が効く
2. expansion signature が意図せず変わらない
3. manual と batch で実行対象 query が一致する
4. provider ごとの総質問数上限を超えない

完了条件:
- 拡張質問の戦略がコード直書きに閉じない
- caching のための順序制御が明示化される

### Phase 3: Deterministic Scoring

目的:
- LLM 自己採点依存を下げる

対象ファイル:
- `analysis_lib.py`
- `llmo_client.py`
- `storage.py`
- `app.py`

実装手順:
1. `raw_llm_score` を保持する列または payload 項目を追加する
2. `deterministic_score` を算出する関数を追加する
3. `visibility verdict` を deterministic 側から計算する
4. 既存の export と UI を deterministic 側に寄せる
5. LLM score は detail 用の参考値に下げる

自己テスト:
1. 自社 citation が増えると score が上がる
2. 自社 hit がない場合に高得点になりすぎない
3. competitor dominance で verdict が逆転しない
4. 過去 row の backfill が破綻しない

完了条件:
- UI 主表示が deterministic score で動く
- LLM score が補助情報に下がる

### Phase 4: Variance Metrics

目的:
- 反復実行の揺れを測る

対象ファイル:
- `analysis_lib.py`
- `app.py`
- `storage.py`
- `exports` 生成部

実装手順:
1. run rollup に `median / min / max / stddev` を追加する
2. `揺れ幅が大きい` 判定を追加する
3. 主画面には `揺れ注意` だけを短く出す
4. 詳細タブで分散指標を見せる
5. export に variance 項目を追加する

自己テスト:
1. 同一 run の score 分布が正しく集計される
2. 反復数 1 件でも落ちない
3. 空データでも UI が壊れない

完了条件:
- run ごとの揺れを UI と export の両方で確認できる

### Phase 5: UI Simplification

目的:
- Nielsen 10 原則と Hick の法則に合う UI へ整理する

対象ファイル:
- `app.py`
- 必要なら `assets/*`
- 必要なら `README.md`

実装手順:
1. 主画面の情報量を棚卸しする
2. 初期画面の主役カードを 3 枚に固定する
3. 補助説明を削るか detail へ移す
4. 主CTA を `分析を実行` に固定する
5. Batch / 定期チェック / 保存導線を `運用` タブに整理する
6. 結果詳細の階層を `結論 -> 根拠 -> 深掘り` に揃える
7. error message を短文化する

自己テスト:
1. 初見で `何を入れて何が出るか` が 10 秒以内で読める
2. 主画面で同時に迷わせる CTA が 2 個以下
3. モバイルでカードの縦崩れがない
4. 文字量が多い説明が主画面に残っていない

完了条件:
- 主画面の認知負荷が明確に下がる
- 詳細機能を消さずに初見導線を軽くできる

### Phase 6: Final Verification

目的:
- 完走後の動作確認を行う

対象:
- manual run
- batch submit / refresh / import
- question set save / load
- schedule save / duplicate / diff
- export
- detail tabs

動作テスト:
1. `py_compile`
2. `import app`
3. HTTP 200
4. manual run 1 回
5. question set 保存 / 読込
6. schedule 保存 / 複製 / diff
7. batch submit 相当
8. batch status refresh
9. batch import
10. export file 生成
11. desktop screenshot
12. mobile screenshot
13. batch で 1 provider 未完の暫定表示を確認

完了条件:
- 主要導線が一通り動く
- 新しい score / variance / UI 文法が一貫している

## 8. Stop Rules

- 3 回自己修正しても直らない場合、その Phase は停止する
- OpenAI の現行導線を壊した場合は、その commit 相当の変更を見直す
- UI の情報量を減らすために主要機能を隠しすぎた場合は停止する
- deterministic score が既存の意味と大きく矛盾する場合は停止する

## 9. File Ownership Guidance

### Core Logic

- `analysis_lib.py`
- `llmo_client.py`
- `query_planning.py`
- `config.py`

### Persistence

- `storage.py`

### UI

- `app.py`

### Docs

- `docs/SAAS_IMPLEMENTATION_PLAN_2026-04-03.md`
- 必要なら `docs/CURRENT_STATE_2026-03-30.md`
- 必要なら `README.md`

## 10. Deliverables

必須 deliverables は次です。

1. provider capability registry
2. deterministic score
3. variance 指標
4. 認知負荷を下げた UI
5. 完走後の動作テスト結果
6. billing_rules / plan_catalog / run_policy の分離

## 11. End Report Format

作業完了時は次を必ず報告する。

1. 読んだ正本ファイル
2. 実施した Phase
3. 変更したファイル
4. 自己テスト結果
5. 3 回自己修正が発生した箇所
6. 未完了項目
7. AGENTS / DOC_STATUS / CURRENT_STATE / README / WORKLOG 更新有無

## 12. Decision On Hardcoding

結論:

- `バッチへの投げ方`
- `prompt caching の方法`
- `拡張質問の戦略`

はハードコーディングを避けた方がよい。

理由:

1. provider ごとの差が大きい
2. 将来の仕様変更に弱い
3. UI とロジックが密結合になる
4. 低性能モデルが修正時に壊しやすい

ただし次は hard-code でもよい。

1. 初期の OpenAI 既定値
2. UI の文言
3. 既定の安全上限

要するに、`provider固有の運用仕様` は設定と adapter に逃がし、`製品として固定したい体験` だけを UI と app に残す。

## 13. Packaging Assumptions

現時点で想定するプラン例:

- PoC
  - OpenAI のみ
  - 手動確認中心
- Light
  - 週2回
  - OpenAI のみ
  - 1実行あたり拡張質問込み合計 50 問
- Upper plan
  - 週3回
  - OpenAI 30 / Gemini 30 / Claude 15
  - batch と prompt caching を使える範囲で使う

表示ルール:

- AI モデル名は user-facing UI に出さない
- provider ごとの返答全文も主画面には出しすぎない
- batch は 3 provider の結果が揃えば通常表示
- 24時間経過後に未完がある場合は、返った分のみ表示し、未完 provider は灰色表示
- 手動実行は返った順に順次表示する
