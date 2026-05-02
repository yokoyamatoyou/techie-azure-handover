# SaaS First Prompt 2026-04-03

更新日: 2026-04-03  
用途: 別ウインドウで `kotomegane` の SaaS 実装作業を開始するときに、そのまま貼って使う開始プロンプト

## Prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\kotomegane\AGENTS.md
- C:\tetie\kotomegane\docs\DOC_STATUS.md
- C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md
- C:\tetie\kotomegane\docs\SAAS_IMPLEMENTATION_PLAN_2026-04-03.md

今回の実施範囲:
- `kotomegane` だけを対象にする
- 今回は `aio2-main` と `notecode` の実装には触れない
- 目的は `PoC` から `企業向けSaaSとして通用する構造` へ寄せること
- 今日はデザインの作り直しではなく、`SaaS 実装計画に沿った着手` を行う

source-of-truth priority:
1. C:\tetie\AGENTS.md
2. C:\tetie\kotomegane\AGENTS.md
3. C:\tetie\kotomegane\docs\DOC_STATUS.md
4. C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md
5. C:\tetie\kotomegane\docs\SAAS_IMPLEMENTATION_PLAN_2026-04-03.md
6. C:\tetie\kotomegane\README.md
7. C:\tetie\kotomegane\app.py
8. C:\tetie\kotomegane\analysis_lib.py
9. C:\tetie\kotomegane\storage.py
10. C:\tetie\kotomegane\config.py
11. C:\tetie\kotomegane\llmo_client.py
12. C:\tetie\kotomegane\query_planning.py
13. C:\tetie\kotomegane\scheduler_runtime.py
14. C:\tetie\kotomegane\docs\SAAS_FIRST_PROMPT_2026-04-03.md

開始時に必ず読むファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\kotomegane\AGENTS.md
3. C:\tetie\kotomegane\docs\DOC_STATUS.md
4. C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md
5. C:\tetie\kotomegane\docs\SAAS_IMPLEMENTATION_PLAN_2026-04-03.md
6. C:\tetie\kotomegane\README.md
7. C:\tetie\kotomegane\app.py
8. C:\tetie\kotomegane\analysis_lib.py
9. C:\tetie\kotomegane\storage.py
10. C:\tetie\kotomegane\config.py
11. C:\tetie\kotomegane\llmo_client.py
12. C:\tetie\kotomegane\query_planning.py

今回の重要な固定仕様:
- provider 差分は hard-code せず、capability / strategy / adapter に寄せる
- user-facing UI に AI モデル名は出さない
- user-facing UI に provider ごとの返答全文を出しすぎない
- 主画面は `入力 -> 結論 -> 深掘り` の 3 段導線を守る
- Nielsen 10 原則と Hick の法則を UI 判断基準に使う
- 主画面の主役カードは 3 枚まで
- batch の別料金は `batch 作成時点で 1 単位消費`
- `コトメイク` 手動は 1 回 1 クレジット
- `コトミガキ` 手動は 1 回 1 クレジット
- `コトメガネ` 手動は 1 回 2 クレジット
- 手動課金は将来の柔軟性のため `service x mode x provider_count` で扱う前提
- `コトメガネ` batch は手動クレジットとは別管理
- batch は 3 provider の結果が揃えば通常表示
- batch で 24 時間以内に一部しか返らない場合は、返った分のみ暫定表示し、未完 provider は灰色表示
- 手動実行は返った順に順次表示する
- 手動実行中は progress bar か spinner で状態説明を出す

現在の想定 provider / model:
- OpenAI: gpt-5.4-nano
- Gemini: gemini-3.1-flash-lite-preview
- Claude: claude-haiku-4-5

現在の想定実行数:
- 手動 OpenAI: 拡張質問込み合計 30
- 手動 Gemini: 拡張質問込み合計 30
- 手動 Claude: 拡張質問込み合計 15
- Light plan: OpenAI のみ、1実行あたり拡張質問込み合計 50

今回の実装方針:
- `Phase 0 -> Phase 1 -> Phase 2 ...` の順で進める
- 各 Phase は `実装 -> 自己テスト -> 失敗時の自己修正 -> 完了判定` を守る
- 同一 Phase の自己修正は 3 回まで
- 3 回失敗したら、その Phase は停止し、未完として報告する
- 完走後は必ず動作テストを行う

今回の最優先:
1. `Phase 1: Provider Capability Registry`
2. `Phase 2: Query Planning And Cache Strategy Refactor`
3. 余力があれば `Phase 3: Deterministic Scoring` に着手

Phase 1 で必ずやること:
- provider catalog に capability 項目を追加する
- provider ごとの default model を registry に移す
- provider ごとの default total question budget を registry に移す
- batch timeout と partial display policy を registry に移す
- OpenAI / Gemini / Claude の差分を if 文の散在ではなく registry 経由に寄せる

Phase 2 で必ずやること:
- query expansion の設定値を config 化する
- provider ごとの expansion 制限値を参照できるようにする
- prompt caching を効かせる送信順序を関数化する
- Batch と通常実行で同じ execution plan を使えるようにする
- `拡張質問込みの合計質問数` を超えないよう planner 側で enforce する

今回の do-not:
- `aio2-main` と `notecode` の実装に触れない
- AI モデル名を user-facing UI に出さない
- provider ごとの batch / cache 条件を UI や app に直書きし続けない
- いきなり scoring 全体や UI 全体を作り直さない
- まず実装せずに延々と設計だけ続けない

開始直後の作業順:
1. 短い計画を作る
2. 現行 `config.py`, `llmo_client.py`, `query_planning.py`, `app.py` の provider 差分と責務境界を確認する
3. `Phase 1` の変更範囲を確定する
4. 実装する
5. 自己テストする
6. 必要なら 3 回まで自己修正する
7. `Phase 2` へ進む

最低限の自己テスト:
1. `.venv\\Scripts\\python.exe -m py_compile app.py analysis_lib.py config.py llmo_client.py storage.py query_planning.py scheduler_runtime.py`
2. `.venv\\Scripts\\python.exe -c "import app"`
3. `http://127.0.0.1:8083/` が 200 を返すこと
4. OpenAI の既存 manual run 導線を壊していないこと
5. Batch 導線を壊していないこと

完了時に必ず報告すること:
- 読んだ正本ファイル
- 実施した Phase
- 変更したファイル
- 自己テスト結果
- 3 回自己修正が発生した箇所
- 未完了項目
- AGENTS / DOC_STATUS / CURRENT_STATE / README / WORKLOG 更新有無
```
