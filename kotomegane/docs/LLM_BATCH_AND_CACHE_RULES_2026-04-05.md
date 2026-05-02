# LLM Batch And Cache Rules 2026-04-05

## Purpose

この文書は、`コトメガネ` における `manual / batch / scheduled batch` と prompt caching の current rule を 1 枚にまとめた運用文書です。

## Run Modes

### Manual

- 主導線は `分析を実行`
- 返答が来た順に順次表示する
- prompt caching を使う前提
- Batch の代替ではない

### Batch

- UI 上の `まとめて確認`
- provider ごとの Batch API を使う
- 1 件ごとの request body は通常実行と同じ分析 payload を使う
- `prompt caching の置き換え` ではなく、`大量投入の分離` として扱う
- 結果は import 後に通常実行と同じ保存経路へ入れる

### Scheduled Batch

- UI 上の `定期チェック`
- 保存済み質問セットを前提に provider batch を投入する
- poll / import を runtime が自動で行う
- in-process scheduler 前提で、外部 service 化は未着手

## Shared Execution Rule

- `manual / batch / scheduled batch` は同じ execution plan を使う
- query planning、短文化、拡張質問、query identity の持ち方は共通
- query order は `query_then_repeat`
- 同じ質問を連続送信し、prompt caching 効率を優先する

## Query Plan Rule

- 長文質問は内部で短文化してよい
- 拡張質問は provider ごとの上限と run 全体の総質問数上限の範囲で作る
- query plan 再利用は `planner_signature` 一致時のみ許可する
- `user_query_raw` と `executed_query` は分けて保存する

## Provider Rules

| provider | live | batch | cache rule | current note |
|---|---|---|---|---|
| OpenAI | yes | yes | explicit prompt cache | `prompt_cache_key` を使う。`24h` は対応モデルのみ有効、未対応時は `in_memory` へ補正 |
| Gemini | yes | yes | implicit cache default | `Gemini 2.5+` は implicit caching が既定。explicit cache は `1時間` 前提、Batch でも context caching 有効 |
| Claude | yes | yes | automatic prompt cache | automatic cache は `5分`。`1時間` cache は未接続、Batch の cache hit は best-effort |

## OpenAI Rule

- API は `Responses API`
- tool は `web_search`
- `prompt_cache_key` を送る
- `prompt_cache_retention=24h` を優先要求する
- モデルが `24h` 非対応なら `in_memory` に自動補正する
- 通常実行で caching を使い、Batch は別導線として扱う

## Gemini Rule

- `Google Search grounding` を使う
- manual/live と provider batch の両方に対応
- cache policy は `provider既定` として表示する
- current implementation では prompt cache の明示指定より provider 既定挙動を優先する

## Claude Rule

- `Messages API + web search tool` を使う
- manual/live と provider batch の両方に対応
- current implementation では automatic cache `5分` を前提にする
- `1時間` cache は未接続

## Batch Import Rule

- batch 結果は `batch_job` と `batch_job_item` で追跡する
- import 後は `keyword_result` 保存へ流す
- `completed` なら import 可
- provider policy 上の partial display が許可される場合、timeout 後に未完 provider を灰色表示する

## Partial Display Rule

- manual は `sequential_progressive`
- batch / scheduled batch は `partial_after_timeout_gray_pending`
- current threshold は provider ごとに `24h`

## Plan And Pricing Rule

- 実行可否は `run_policy.py`
- provider ごとの総質問数上限は `plan_catalog.py`
- 内部 billing unit は `billing_rules.py`
- ただしこれらは現時点では `内部運用ルール` であり、正式料金表ではない

## Source Of Truth

- provider registry: `config.py`
- run mode policy: `run_policy.py`
- OpenAI request / batch body: `llmo_core/openai_client.py`
- runtime context: `runtime/common.py`
- product-level explanation: `README.md`

## Known Gaps

- Gemini live batch は quota 429 のため完走確認待ち
- Claude live smoke は API key 設定環境での確認が未了
- external scheduler / worker への分離は未着手
- provider ごとの cache behavior は今後仕様変更の影響を受ける可能性がある
