# separate window execution prompt company intro source handoff audit 2026-04-21

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md

今回の依頼種別:
- separate window execution prompt
- `COMPANY_INTRO_SOURCE_HANDOFF_AUDIT`
- 主題は company introduction の source handoff
- repair / output guard を初手でいじるのではなく、source -> writer handoff の実態確認を先にやる

今回の目的:
- `branding/company_introduction` で source があるのに `source_grounding_items` が空になる経路を特定する
- `source_inputs -> source_documents -> source_grounding_items -> prompt -> used facts` のどこで情報が落ちるかを end-to-end で説明できるようにする
- `事業内容 / 強み / 歩み` を source-backed に writer へ渡せているか検証する
- 必要なら owner-local な最小修正で、company introduction の source handoff を改善する
- repair / quality guard 側の symptom patch を初手にしない

今回の実施範囲:
- company introduction の source handoff と prompt handoff
- current success path は壊さない
- owner scope は source / contract / prompt handoff の direct surface に留める

今回の authoritative evidence:
- blocked run:
  - attempt_id = `gen-e451e736`
  - timestamp = `2026-04-21 00:16:11 JST`
  - runtime_reason_code = `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - source_count = `5`
  - `source_grounding_item_count = 0`
  - `must_cover_reflection_rate = 0.3333`
  - `source_trace_coverage = 0.1667`
  - output_guard reasons:
    - `contract_alignment_must_cover_reflection_rate<0.50`
    - `source_grounding:weak_reflection`
    - fingerprint warnings
- follow-up run:
  - attempt_id = `gen-live-rerun-20260421-contract-root-audit`
  - timestamp = `2026-04-21 01:35:14 JST`
  - runtime_reason_code = `OK`
  - `repair_applied = true`
  - `source_grounding_item_count = 0`
  - `must_cover_reflection_rate = 0.6667`
  - `output_guard.blocked = false`
- shared observation:
  - URLs は入っているのに、writer に渡る source-backed facts が薄い疑いが強い

今回の初手で確認すること:
1. blocked run / rerun の `input_contract.source_inputs` と `source_documents` の差分
2. `source_grounding_status` がなぜ `not_required` になるのか
3. `source_grounding_items` がどこで空になるのか
4. writer prompt に source-backed fact lines がどの程度入っているか
5. company introduction の `must_cover = 事業内容 / 強み / 歩み` が source と結びついているか
6. `used_fact_ids` または同等 telemetry で、writer が何を使ったか追えるか

このウインドウで最初に読む証跡:
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\latest_generation_quality_report.json
- C:\tetie\notecode\logs\generation_audit_log.jsonl
- 必要なら:
  - C:\tetie\notecode\logs\app.log

このウインドウで読むべきコード:
- primary:
  - C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
  - C:\tetie\notecode\note\current_mainline_runner.py
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - C:\tetie\notecode\note\tests\test_newalgorithm_phase01_contract.py
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
- secondary if needed:
  - C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - C:\tetie\notecode\note\natural_blog_core.py
- 参照のみ:
  - C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py

今回の root hypothesis candidate:
1. source URL は input されているが、company introduction では source grounding が `not_required` 側に落ち、writer に source-backed facts が渡っていない
2. `source_documents` への hydration と `source_grounding_items` 生成の間に company introduction 専用の drop がある
3. `must_cover` は入っているが source bucket と結びつかず、generic writer が一般論で埋めて fingerprint warning を増やしている
4. repair は一部救えても、source handoff が弱いままだと根本改善にならない

今回の禁止:
- output_guard.py の閾値変更
- strict_saas_mode の変更
- quality guard first
- repair prompt / acceptance の symptom patch first
- formatter / regex / UI wording の延命
- article_type 固定ルーティング table の追加
- unrelated cleanup
- AGENTS / WORKLOG / plan docs 更新

root fix と認める条件:
- source handoff の落下点を call chain で説明できる
- company introduction で source がある run では、`source_grounding_items` か同等の writer-facing fact bundle が空のまま通らない
- `事業内容 / 強み / 歩み` の少なくとも一部が source-backed に prompt へ渡る
- blocked run の主因が `source grounding weak reflection` だったことを before / after で比較できる
- 変更が owner-local で rollback 可能

最初の作業手順:
1. `gen-e451e736` と `gen-live-rerun-20260421-contract-root-audit` の source handoff telemetry を比較する
2. `input_contract -> current_mainline_runner -> prompt_builder` の source handoff map を作る
3. `company introduction source handoff drop points` を列挙する
4. 各 drop point を
   - source ingest
   - source hydration
   - source grounding extraction
   - prompt handoff
   - writer consumption
   に分類する
5. 1 本の root hypothesis に絞る
6. 必要なら最小 diff を実装する
7. focused tests -> owner-local tests -> exact rerun を行う

このウインドウで最低限ほしい telemetry:
- source_inputs count
- hydrated source_documents count
- source_grounding_status
- source_grounding_items count
- source grounding drop reason
- must_cover -> source bucket mapping
- writer prompt に入った source fact lines
- writer が実際に使った fact ids / anchor ids

allowed touched files:
- production:
  - C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
  - C:\tetie\notecode\note\current_mainline_runner.py
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- tests:
  - C:\tetie\notecode\note\tests\test_newalgorithm_phase01_contract.py
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py

do-not-touch unless absolutely proven necessary:
- C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
- C:\tetie\notecode\plan\...
- AGENTS / WORKLOG

implementation policy:
- まず source handoff を見える化する
- source があるのに grounding が空のまま通る path を優先的に疑う
- generic filler を減らし、source-backed fact を prompt に落とす方向を優先する
- company introduction だけの ad-hoc wording patch は避ける
- repair で救う前に generation input を正す

tests / checks:
- focused:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase01_contract.py -k "company or source_grounding or source_trace" -q
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "company_intro or source_grounding or must_cover or prompt" -q
- owner-local:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase01_contract.py note\tests\test_simple_note_pipeline.py -q
- 必要なら:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py -k "company or branding" -q

live rerun:
- exact same company introduction input line で rerun する
- before / after で最低限比較する項目:
  - runtime_reason_code
  - output_guard.blocked
  - source_grounding_item_count
  - source_grounding_reflection_ratio
  - must_cover_reflection_rate
  - source_trace_coverage
  - title / lead / first section が current-business-first を維持するか

stop conditions:
- source handoff ではなく output_guard 閾値変更しか残らない
- multiple owner simultaneous reopen が必要
- input_contract / prompt_builder owner を超えないと前進できない
- rerun 主因が別系統へ移る
- root fix を説明できず telemetry accretion だけが残る

最終報告フォーマット:
1. 読んだ正本 / 証跡 / コード
2. source handoff end-to-end map
3. drop point の特定結果
4. root hypothesis
5. touched files
6. 実装内容
7. 実行した tests と結果
8. live rerun attempt id / timestamp / exact outcome
9. before / after
   - source_grounding_item_count
   - must_cover_reflection_rate
   - source_trace_coverage
   - output_guard blocked / reason
10. まだ残る warning
11. 残リスク
12. AGENTS / WORKLOG / plan docs 更新要否

最終報告で必ず明記すること:
- source はどこまでログで追えたか
- source を生成側へ渡す chain のどこで落ちていたか
- 主因が
  - 編集段階
  - 初回生成品質
  - source handoff
  のどれだったか
- current patch が root fix か symptom patch か
- close と言ってよいか、まだ言えないか
```
