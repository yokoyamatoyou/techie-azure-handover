# Task Mapping

## Requested Task

- 最短で見栄えのある PoC
- config でパラメータ管理
- キーワードを `n` 回回して分析
- `n` は UI で変更可能
- prompt caching を使う
- `gpt-5.4-nano` を前提にする
- 仮想環境構築と起動導線を用意
- markdown ドキュメントも作る

## Implemented Shape

- `Responses API + web_search + GPT-5.4 nano`
- config JSON 永続化
- UI-controlled `n`
- SQLite persistence
- question set persistence
- scheduled batch runtime
- raw answer retention (`answer_text` / `citations`)
- raw answer structuring (`mentioned_brands_json` / `citation_domains_json` / `owned_mention_hit` / `competitor_mention_hit` / `answer_type_label`)
- raw answer tuning (brand alias / citation domain normalization / answer type scoring)
- manual `Page Brief` draft from detail card
- manual `Cluster Brief` draft + persistence (`Intent / Page Gap / Question Set`)
- schedule delete / duplicate / diff UI
- schedule / question set scoped `Outcome Compare` (2 run)
- 日本語優先ラベル化 + `入力する / 設定する / 結果を見る` の導線分離
- user-facing cost removal with internal guardrail retained
- trend charts + export
- venv setup scripts
- markdown docs

## Deliberate Simplifications

- 2-stage pipeline was reduced to 1-stage to cut cost and delivery time.
- `Page Brief` / `Cluster Brief` は rule-based draft の初期版で、常時自動生成や LLM ベース再構成は未着手。
- `Outcome Compare` は 2 run 比較の初期版で、settings diff と統合した長期比較は未着手。
- No CSV importer yet.
- In-process scheduler only. Windows service / cron などの外部常駐化は未着手。

## Current UX Tasks

- first view の主役を `入力 / 今回の結論 / 主な参照元サイト / 頻出論点` に固定し、それ以外の説明を弱くする
- left nav と hero の文量を削り、初見で読む場所を迷わせない
- 主結果 3 cards の 1 枚あたりの行数、chip 数、補助文を減らす
- `主な参照元サイト` は raw URL ではなく `ページ名 + サイト名 + 質問数` で見せ、実URLは詳細へ寄せる
- `頻出論点` は質問タイプと混同しないよう、回答と引用ページで繰り返し現れる論点として固定する
- mobile では hero/status/card の縦積みを圧縮し、最初の結論 card までのスクロール量を減らす
- closed の panel / detail block は主結果 card より静かな見た目にする
- 詳細な質問タイプ分析は first view から外し、detail owner に寄せる

## Task Source Of Truth

- 詳細 task と完了条件は `docs/RESULT_UX_IMPLEMENTATION_PLAN_2026-04-14.md` の `2026-04-20 Nielsen Review Addendum` を参照
