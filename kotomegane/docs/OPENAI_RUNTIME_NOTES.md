# OpenAI Runtime Notes

最終確認日: 2026-03-30

この PoC は以下の現行前提で組んでいる。

- モデル既定: `gpt-5.4-nano`
- API: Responses API
- ツール: `web_search`
- prompt caching: `prompt_cache_key` を使用
- retention 既定: `in_memory`
- reasoning 既定: `low`
- UI port 既定: `8083`

## Official References

- Models
  - https://developers.openai.com/api/docs/models/all
- Responses API
  - https://platform.openai.com/docs/api-reference/responses/compact/
- Web Search guide
  - https://platform.openai.com/docs/guides/tools-web-search?api-mode=responses&lang=python
- API pricing
  - https://openai.com/api/pricing/

## Pricing Assumptions In Code

- input: `$0.20 / 1M`
- cached input: `$0.02 / 1M`
- output: `$1.25 / 1M`
- web search tool call: `$10 / 1K calls`

必要なら `config.py` の `PricingConfig` を更新する。

## Runtime Notes From Actual Verification

- 現行 Responses API では `web_search` と `reasoning.effort='minimal'` を併用できなかった。
  - そのため config 既定値は `low`。
  - 互換のため、古い設定が残っても `llmo_client.py` で `minimal -> low` に補正する。
- 現行 Responses API では `tools[0].allowed_domains` を受け付けなかった。
  - そのため `allowed_domains` は tool parameter ではなく user payload 側の soft constraint として渡す。
  - UI 表示も `Allowed domains (soft preference)` に統一した。
  - hard filter ではないため、指定外ドメインが citation に出る可能性は残る。

## API Key Resolution

- `.env` の `OPENAI_API_KEY` は `python-dotenv` で読み込む
- ただし既存の process / user / machine 環境変数がある場合は、その値を優先する
- `.env` が空でも環境変数があれば起動できる
- `run.ps1` は起動前に、`.env` か環境変数か、どちらを使うかを表示する

## Provider Runtime Boundary

- live runtime は `OpenAI` のみ
- `Gemini` `Claude` `Perplexity` は provider catalog と adapter 入口だけ先に追加している
- 実 API をつなぐ場合は `llmo_client.py` の provider factory に adapter を追加する


