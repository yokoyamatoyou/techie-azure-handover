# Kotomegane SaaS Registry Review 2026-04-03

## 目的

`kotomegane` の 2026-04-03 実装で入れた次の変更が妥当かを、別AIにレビューしてもらうための質問集です。

1. Provider capability registry の設計
2. Query planning と execution plan の責務分離
3. Manual / batch / scheduled batch の整合
4. 回帰リスク

## これは何のソフトか

- `kotomegane` は、企業が「AI回答の中で自社がどれだけ見えているか」を確認するための可視化 SaaS / PoC です。
- ユーザーは `質問` `自社URL` `ブランド名` を入れます。
- システムは LLM + web search を使って回答を集め、`自社が出たか / 外部サイトが優勢か / 次に直すページは何か` を判断材料として返します。
- 主用途は SEO ツールというより、`AI検索・AI回答でのブランド露出確認` と `改善優先度の判断` です。
- 現在の UI 方針は `入力 -> 結論 -> 深掘り` の 3 段導線です。
- 現在 live なのは OpenAI 系だけで、Gemini / Claude は planned 状態です。
- 今回レビューしてほしいのは、見た目ではなく `provider 差分の設計`, `query planning`, `manual/batch/scheduled の実行整合` です。

## このレビューで見てほしい判断軸

- このソフトは「単発の LLM チャット」ではなく、同じ質問群を繰り返し測定し、比較可能な形で保存する運用ツールとして成立しているか
- provider ごとの差分が UI や app 本体に散らず、registry / planner / adapter に閉じる方向になっているか
- 将来 Gemini / Claude を live 化するときに、今回の設計が足場として妥当か
- OpenAI の現行 manual run / batch run / scheduled batch を壊していないか

## 前提

- 元ファイルは変更せず、このフォルダにはコピーだけ置いています。
- 今回は `kotomegane` だけが対象です。
- アップロード数制限のため、運用ルールと現況要約はこのファイル内にまとめています。

## 省略した正本の要約

- 全体ルール:
  - `C:\tetie\AGENTS.md` を起点にする
  - 今回は `kotomegane` だけ対象
  - `aio2-main` と `notecode` の実装には触れない
- `kotomegane` の運用ルール:
  - `PoC` から `企業向けSaaSとして通用する構造` へ寄せる途中段階
  - user-facing UI にモデル名は出さない
  - provider 差分は hard-code ではなく capability / strategy / adapter に寄せる
  - 主画面は `入力 -> 結論 -> 深掘り` の 3 段導線を守る
- 2026-04-03 の実装方針:
  - Phase 1 は provider capability registry
  - Phase 2 は query planning / cache strategy refactor
  - 最優先は `OpenAI 30 / Gemini 30 / Claude 15` の総質問数上限を provider registry へ寄せること
  - manual / batch / scheduled batch で同じ execution plan を使うこと
- 現在の実装状態:
  - OpenAI のみ live
  - Gemini / Claude は planned
  - 今回の変更で provider registry に `default model / total question budget / batch timeout / partial display policy / cache policy / expansion mode` を追加
  - `query_planning.py` で provider ごとの上限を見て expansion 数を制御
  - `app.py` と `scheduler_runtime.py` は同じ execution plan を使うように変更

## 今回アップロードする 7 ファイル

1. `RESEARCH_QUESTIONS_2026-04-03.md`
2. `SAAS_IMPLEMENTATION_PLAN_2026-04-03.md`
3. `config.py`
4. `query_planning.py`
5. `llmo_client.py`
6. `app.py`
7. `scheduler_runtime.py`

## レビュー依頼

### 1. Provider registry

- `config.py` の provider registry に持たせた項目は、Phase 1 の目的に対して十分ですか。
- `default model / total question budget / batch timeout / partial display policy / cache policy / expansion mode` の置き場所は適切ですか。
- `AppConfig` に置いた query planning 設定値と provider registry の責務分離に不自然さはありますか。

### 2. Query planning

- `query_planning.py` の `prepare_query_plan(...)` が provider ごとの総質問数上限を見て expansion を抑える設計は妥当ですか。
- `build_execution_plan(...)` で manual / batch / scheduled batch の送信順序を共通化した設計に破綻はありませんか。
- `query_then_repeat` を共通既定値にしている点は prompt caching 目的に対して適切ですか。

### 3. Batch / scheduler 整合

- `llmo_client.py` の batch request 生成を `execution_requests` ベースにしたことで、manual/batch/scheduled で対象 query がずれない実装になっていますか。
- `scheduler_runtime.py` が `app.py` と同じ execution plan を使うようにした変更に見落としはありませんか。
- provider が batch 非対応のときの停止条件は適切ですか。

### 4. 回帰リスク

- OpenAI の既存 manual run を壊す可能性がある箇所はどこですか。
- OpenAI の既存 batch 導線を壊す可能性がある箇所はどこですか。
- 実装上のバグ、境界条件、設計上の不整合があれば優先度順に挙げてください。

### 5. 次フェーズ判断

- この実装を前提に Phase 3 `Deterministic Scoring` へ進んでよいですか。
- 先に追加で補強すべき点があれば、最小単位で提案してください。

## 最低限見てほしいファイル

- `RESEARCH_QUESTIONS_2026-04-03.md`
- `SAAS_IMPLEMENTATION_PLAN_2026-04-03.md`
- `config.py`
- `query_planning.py`
- `llmo_client.py`
- `app.py`
- `scheduler_runtime.py`
