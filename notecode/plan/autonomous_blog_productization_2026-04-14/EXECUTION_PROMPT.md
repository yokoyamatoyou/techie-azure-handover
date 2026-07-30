# autonomous_blog_productization_2026-04-14 EXECUTION PROMPT

## next startup use

- 次回 separate window 起動時は、このファイルの `prompt` ブロックをそのまま使う
- current keep-state は `naturalness_recovery_2026-04-07` と `ui_prompt_distillation_autonomous_2026-04-14` を正として扱う
- この package は separate execution line であり、current package の continuation とみなさない
- source-less WEB mode は allowed categories に限定し、company intro と announcement へ広げない
- UI minimalism は Nielsen 10 と Hick's Law に照らして評価する
- prompt accretion と module accretion は default remedy にしない
- same hypothesis unchanged retry は 3 回まで
- phase pass 後は user 待ちせず次 phase へ進む
- autonomous 完走後は final categories を生成し、Codex 視認評価まで行う

## prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\README.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\TASK.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\PROGRESS.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\ROLLBACK.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\EXECUTION_PROMPT.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\README.md
- C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\PROGRESS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md

開始時に必ず確認する artifact:
- C:\tetie\notecode\logs\latest_generation_output.txt
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\latest_generation_quality_report.json

今回の mission:
- separate execution line として `minimal UI + source-less web-grounded generation + autonomous completion loop` を実装する
- current success path
  - C:\tetie\notecode\note\current_mainline_runner.py
  - -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  を維持する
- source 無しでも `daily_story / explanatory_article / industry_analysis` は WEB検索で一次情報または一次情報に近い current sources を集め、source-backed generation に変換する
- `branding/company_introduction` と `announcement` は source-backed を維持し、source-less auto generation へ広げない
- UI は first view の文字数を極小化し、`どこに出すか / 何を書くか / 何から書くか` の 3 decisions と 1 行入力で開始できるようにする
- phase 完了ごとに tests を実行し、同一仮説の失敗は 3 回まで自己修正する
- 3 回失敗したら rollback して停止し、user report を出す
- phase pass 後は自律継続し、最後まで完走を目指す
- autonomous 完走後は
  - `company_introduction`
  - `explanatory_article`
  - `announcement`
  の 3 blog を生成し、Codex が本文を視認して評価する
- さらに source-less WEB mode の representative case を 1 つ生成し、WEB trace と一緒に評価する

fixed operational rules:
- `1 phase = 1 narrow hypothesis = 1 owner scope = 1 rollback unit`
- same hypothesis unchanged retry は 3 回まで
- prompt accretion 禁止
- module accretion 禁止
- 新 helper は 1 phase 1 個まで。既存 owner に安全な置き場がなく、より大きい inline logic を避ける場合だけ許可
- current keep-state package を壊さない
- completed reference package を reopen しない
- current な WEB情報を扱うときは relative date を信用せず exact date を保存する
- primary / official source を優先し、まとめサイトや匿名転載だけで通さない
- source trace が不足したら fail-closed する
- `branding/company_introduction` と `announcement` は source-less WEB mode を拒否する
- title は first screen に出さない

phase order:
1. Phase 01 Minimal UI Journey
   - owner: C:\tetie\notecode\note\note_writer_app.py
   - goal: first view を `3 decision groups + 1 text input + 1 CTA` へ縮退
2. Phase 02 Source Mode Contract Narrowing
   - owner: C:\tetie\notecode\note\input_contract_v1.py
   - goal: `source_mode / web_research_allowed / industry_hint / source_trace_policy` を bounded contract に固定
3. Phase 03 WEB Research To Source Documents
   - owner: C:\tetie\notecode\note\current_mainline_runner.py
   - goal: source-less WEB mode を current mainline の `source_documents` へ hydrate
4. Phase 04 Distilled Brief For WEB-Grounded Generation
   - owner: C:\tetie\notecode\note\simple_note_pipeline\ui_prompt_distillation.py
   - goal: WEB digest を prompt bloat なしで generation に渡す
5. Phase 05 Guard And Trace Enforcement
   - owner: C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py
   - goal: category boundary / source trace / stale source guard を fail-closed 化
6. Phase 06 Fixed Evaluation Battery And Codex Visual Review
   - owner: C:\tetie\notecode\note\current_mainline_ui_matrix.py
   - goal: final categories と WEB mode representative case を固定し、visual review まで完走

phase protocol:
1. phase 開始前に、current baseline / hypothesis / owner / rollback intent を短く書く
2. owner-local edit を行う
3. owner-local tests を実行する
4. shared checks を実行する
5. failure があれば原因を narrow に切り、同一仮説で最大 3 回まで自己修正する
6. 3 回失敗したら rollback して停止し、user report を出す
7. pass したら `PROGRESS.md` と `ROLLBACK.md` を更新し、そのまま次 phase へ進む

shared checks:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q

UI acceptance principles:
- visibility of system status:
  - 状態表示は短く、progress が見える
- match with real world:
  - `出す / 書く / 材料` の短語で迷わない
- error prevention:
  - `announcement` は required facts 不足で止める
  - blocked categories で WEB mode を止める
- recognition over recall:
  - options は first view に見える
- minimalist design:
  - first view に不要な設定文を並べない
- Hick's Law:
  - visible primary groups は 3、各選択肢は 3〜5 を目安にする

WEB mode acceptance rules:
- allowed categories only
- source query / URL / publisher / exact date / excerpt を trace として残す
- dated source documents に hydration できない場合は fail-closed
- official / primary source が 0 の場合は `summary only` で進めない
- legal / medical / investment advice を source-less experimentation の main target にしない

final evaluation battery:
- source-backed:
  - `branding/company_introduction`
  - `explanatory_article`
  - `announcement`
- source-less WEB:
  - `daily_story` or `explanatory_article`

final evaluation output:
- generated text artifact
- tests run
- WEB mode source trace
- Codex visual judgment
- verdict:
  - `stable pass`
  - `unstable pass`
  - `unresolved`

Codex visual evaluation points:
- title / lead が説明カードや管理ラベルに見えないか
- paragraph breath が均一すぎないか
- sentence endings が機械的に反復していないか
- current-business-first keep-state を崩していないか
- announcement が事実案内として安全か
- source-less WEB mode が dated facts を自然に使えているか

最終報告で必ず示すこと:
- 読んだ source-of-truth
- 各 phase の hypothesis / owner / tests / retries / keep or rollback
- 追加した helper があれば必要性
- UI minimalism がどの principle に効いたか
- WEB mode の source trace と exact dates
- `company_introduction / explanatory_article / announcement` の visual verdict
- WEB mode representative case の visual verdict
- unresolved risk
- AGENTS / WORKLOG 更新の有無
```
