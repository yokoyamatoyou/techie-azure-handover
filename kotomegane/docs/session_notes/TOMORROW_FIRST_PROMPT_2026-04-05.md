# Tomorrow First Prompt 2026-04-05

更新日: 2026-04-04  
用途: 次回起動時の最初にそのまま貼り、`kotomegane` の責務分割の続きと残 verification を current state に沿って再開するための開始プロンプト

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
- 責務分割の続きと最小 verification
- `aio2-main` と `notecode` には触れない

source-of-truth priority:
1. C:\tetie\AGENTS.md
2. C:\tetie\kotomegane\AGENTS.md
3. C:\tetie\kotomegane\docs\DOC_STATUS.md
4. C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md
5. C:\tetie\kotomegane\docs\SAAS_IMPLEMENTATION_PLAN_2026-04-03.md
6. C:\tetie\kotomegane\README.md
7. C:\tetie\kotomegane\app.py
8. C:\tetie\kotomegane\analysis_lib.py
9. C:\tetie\kotomegane\analysis_core\
10. C:\tetie\kotomegane\llmo_client.py
11. C:\tetie\kotomegane\llmo_core\
12. C:\tetie\kotomegane\scheduler_runtime.py
13. C:\tetie\kotomegane\storage.py
14. C:\tetie\kotomegane\docs\TOMORROW_FIRST_PROMPT_2026-04-05.md

開始時に必ず確認すること:
1. `app.py` の UI責務分離が `ui/` package へ反映済みであること
2. `analysis_lib.py` が facade、実装本体が `analysis_core/` に移っていること
3. `llmo_client.py` が facade、実装本体が `llmo_core/` に移っていること
4. `analysis_core/common.py` が facade、内部実装が `common_constants / text_utils / domain_utils / common_io / scoring` に分かれていること
5. `analysis_core/scoring.py` が facade、内部実装が `classification / deterministic_scoring` に分かれていること

重要な現在値:
- `app.py` の UI責務分離は実装済み
- `analysis_lib.py` の facade 化と `analysis_core/` 分離は実装済み
- `llmo_client.py` の facade 化と `llmo_core/` 分離は実装済み
- `analysis_core/common.py` の横分割は実装済み
- `analysis_core/scoring.py` の facade 化と `classification / deterministic_scoring` 分離は実装済み
- request 数は増やしていない
- prompt 構成は維持している
- OpenAI live manual / batch verification は確認済み
- Gemini manual/live は確認済み
- Gemini live batch は quota 429 で完走未確認
- Claude live smoke は API key 未設定で未確認

今回の主目的:
1. 分割の次段を small step で進める
2. 既存挙動を崩さず verification を積む
3. docs を current state に合わせ続ける

今回の優先順:
1. facade 越し import が壊れていないか `py_compile` / import / HTTP 200 で確認する
2. 余力があれば Claude の `1時間` cache を request payload に接続するか判断する
3. Anthropic key がある環境なら Claude manual/live と batch smoke を行う
4. Gemini quota が戻っていれば live batch の submit / refresh / import 完走を確認する
5. 余力があれば prompt family ごとの重みづけ方針を設計する

やらないこと:
- 新しい大機能を増やさない
- request 数を増やす prompt 再設計をしない
- `aio2-main` と `notecode` を触らない
- UI を再度大きく組み替えない

実行順:
1. docs と current code を確認して短い plan を出す
2. `py_compile`、`import analysis_lib, app`、HTTP 200 を確認する
3. 可能なら Claude の `1時間` cache を request payload に接続するか判断する
4. 可能なら provider verification の未回収分を small smoke で回収する
5. 必要最小限で `README.md` と `docs/CURRENT_STATE_2026-03-30.md` を更新する

最低限の検証:
1. `.venv\\Scripts\\python.exe -m py_compile app.py analysis_lib.py llmo_client.py scheduler_runtime.py storage.py`
2. `.venv\\Scripts\\python.exe -m py_compile analysis_core\\common.py analysis_core\\scoring.py analysis_core\\classification.py analysis_core\\deterministic_scoring.py llmo_core\\factory.py`
3. `.venv\\Scripts\\python.exe -c "from analysis_core.common import classify_keyword_intent, _contains_named_term; import analysis_lib, app"`
4. `http://127.0.0.1:8083/` が 200 を返すこと
5. facade 越しの underscore import が必要ならそれも smoke すること

完了時に必ず報告すること:
- 読んだ正本ファイル
- 今回進めた phase
- 修正したファイル
- verification 結果
- 未着手と次 phase
- docs 更新有無
- AGENTS / WORKLOG 更新要否
```
