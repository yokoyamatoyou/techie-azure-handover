# Tomorrow First Prompt 2026-04-04

更新日: 2026-04-03  
用途: 次回起動時の最初にそのまま貼り、`kotomegane` の残作業を current plan の完了に寄せて再開するための開始プロンプト

## Prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\kotomegane\AGENTS.md
- C:\tetie\kotomegane\docs\DOC_STATUS.md
- C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md
- C:\tetie\kotomegane\docs\SAAS_IMPLEMENTATION_PLAN_2026-04-03.md
- C:\tetie\kotomegane\README.md

今回の実施範囲:
- `kotomegane` のみ
- current SaaS plan の残件整理と完了条件の回収
- `aio2-main` と `notecode` には触れない

source-of-truth priority:
1. C:\tetie\AGENTS.md
2. C:\tetie\kotomegane\AGENTS.md
3. C:\tetie\kotomegane\docs\DOC_STATUS.md
4. C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md
5. C:\tetie\kotomegane\docs\SAAS_IMPLEMENTATION_PLAN_2026-04-03.md
6. C:\tetie\kotomegane\README.md
7. C:\tetie\kotomegane\config.py
8. C:\tetie\kotomegane\plan_catalog.py
9. C:\tetie\kotomegane\billing_rules.py
10. C:\tetie\kotomegane\run_policy.py
11. C:\tetie\kotomegane\app.py
12. C:\tetie\kotomegane\analysis_lib.py
13. C:\tetie\kotomegane\llmo_client.py
14. C:\tetie\kotomegane\storage.py
15. C:\tetie\kotomegane\scheduler_runtime.py
16. C:\tetie\kotomegane\docs\TOMORROW_FIRST_PROMPT_2026-04-04.md

開始時に必ず確認すること:
1. `Phase 1` から `Phase 7` までの実装が docs と一致しているか
2. `plan_catalog / billing_rules / run_policy` 分離後の current state を再確認すること
3. `max_output_tokens=1200` が config と保存設定の両方に反映済みであること
4. `save_keyword_result` の placeholder mismatch 修正後であること

重要な現在値:
- provider capability registry は実装済み
- query planning / cache strategy refactor は実装済み
- deterministic score と variance 指標は実装済み
- UI simplification は実装済み
- `plan_catalog / billing_rules / run_policy` 分離は実装済み
- OpenAI live manual は確認済み
- OpenAI live batch は `submit / refresh / import` まで最小構成で確認済み
- live manual で JSON truncation が出たため、`max_output_tokens` 既定値は `1200`
- `Gemini / Claude` live adapter は current plan 外

今回の主目的:
1. current plan の残件を潰す
2. verification の証跡を増やす
3. 余計な新機能を増やさず、閉じ方を整える

今回の優先順:
1. 最新 phase 後の desktop / mobile screenshot を再取得する
2. `長文短文化` と `拡張検索` を live data で確認し、保持要素と派生質問の自然さを点検する
3. `query_plan` と variance 指標を export / report にどこまで露出するか決める
4. 必要なら最小修正だけ行い、docs を現在値へ追従させる

やらないこと:
- 完了済み phase を大きく作り直さない
- `Gemini / Claude` live adapter に着手しない
- UI をまた大きく組み替えない
- `aio2-main` と `notecode` を触らない

実行順:
1. docs と current code を確認して短い plan を出す
2. screenshot を取り直す
3. live で `長文短文化` と `拡張検索` を確認する
4. export / report 露出方針を決める
5. 必要なら最小修正する
6. `README.md` と `docs/CURRENT_STATE_2026-03-30.md` を更新する

最低限の検証:
1. `.venv\\Scripts\\python.exe -m py_compile app.py analysis_lib.py billing_rules.py config.py llmo_client.py plan_catalog.py query_planning.py run_planning.py run_policy.py scheduler_runtime.py storage.py`
2. `.venv\\Scripts\\python.exe -c "import app"`
3. `http://127.0.0.1:8083/` が 200 を返すこと
4. screenshot が desktop / mobile の両方で取得できること
5. live で `長文短文化` と `拡張検索` を 1 例以上確認すること

完了時に必ず報告すること:
- 読んだ正本ファイル
- 実施した残件
- 修正したファイル
- screenshot の取得有無
- live 確認結果
- docs 更新有無
- AGENTS / WORKLOG 更新要否
```
