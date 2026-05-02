# separate window execution prompt prompt-only live generation smoke 2026-04-23

この prompt は別ウインドウ開始用。`daily_story` / `prompt_only` / sourceなし の live generation smoke だけを実行する。  
実装変更は原則しない。失敗した場合は原因を切り分け、必要なら停止して報告する。

## 目的

- `source_mode="prompt_only"` の live generation が current mainline で実際に動くか確認する。
- UI / runner / simple pipeline の発火点が想定通りか確認する。
- `web` / omakase route に流れないことを確認する。
- source なしでも `daily_story` として成立し、未確認 claim を足さないことを確認する。

## 最初に読む

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\ALGORITHM.md`
  - `## 4. Single-Pass Generation`
  - `## 5. Repair Algorithm`
  - `## 12. Persona / Source Packet / Editing Persona Contract`
- `C:\tetie\WORKLOG.md`
  - `2026-04-23 追記（notecode persona source generation contract autonomous implementation）`
- 実装確認用:
  - `C:\tetie\notecode\note\input_contract_v1.py`
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\note_writer_app.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## 前提

- 実装は完了済み。
- 既存 self tests は pass 済み。
- この window の目的は live generation smoke であり、通常の実装 phase ではない。
- credentials / API key / model access が利用可能かを確認してから実行する。
- cost が発生するため、live case は最初は 1 件だけ。

## 実行ケース

### Case 1: prompt-only daily_story live smoke

条件:

- article type: `daily_story`
- source mode: `prompt_only`
- source documents: none
- source inputs: none
- user prompt:

```text
夕方の打ち合わせで、同じ言葉を使っているのに受け取り方が少しずれた話。次から確認の仕方を一つ変えるところまで書きたい。
```

期待:

- `success=True`
- `runtime_reason_code=OK`
- `source_mode=prompt_only`
- `source_documents=[]`
- `source_trace_policy=prompt_context_not_source`
- `web_research_allowed=False`
- omakase / web trace / AUTO_SOURCE_READY に流れない
- source grounding weak reflection で block されない
- 本文が説明書・要約調に戻らない
- 統計、価格、法律、医療、金融、比較優位、会社実績、顧客名、受賞、成果数値を足さない
- persona 名、editor 名、trial 名、source contract、validation / repair 方針が visible body に出ない

## 推奨実行方法

まずテスト再確認を最小で行う:

```powershell
.\.venv\Scripts\python.exe -m pytest note\tests -k "prompt_only or past_blog or injection" -q
```

その後、既存の live generation 実行導線を調べる:

- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\logs\generation_audit_log.jsonl`
- `C:\tetie\notecode\logs\latest_generation_output.txt`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\latest_generation_quality_report.json`

既存の CLI / script / helper がある場合はそれを使う。  
見つからない場合は、UI 経由で実行してもよい。UI 経由の場合は `C:\tetie\techie-hub\start.bat` または既存起動手順に従い、コトメイク `http://127.0.0.1:8080/` で実施する。

## 確認ログ

live generation 後に必ず確認する。

- `C:\tetie\notecode\logs\latest_generation_output.txt`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\latest_generation_quality_report.json`
- `C:\tetie\notecode\logs\generation_audit_log.jsonl`

確認項目:

- attempt id
- success
- runtime_reason_code
- output_guard_blocked
- source_mode
- article_type
- source_documents count
- source_trace_policy
- web_research_allowed
- quality warnings
- fingerprint warnings
- source grounding diagnostics
- visible body の claim leakage
- visible body の internal-term leakage

## 失敗時の扱い

失敗してもすぐ実装修正しない。まず原因を分類する。

### Stop and report

次は停止して user report。

- credentials / API key / model access がない
- cost approval が必要
- live execution helper が見つからず、UI も起動できない
- `prompt_only` ではなく `web` / omakase に流れる
- `daily_story` 以外へ route が変わる
- source grounding guard が prompt-only を source-backed と誤認して block する
- output guard が未確認 claim を検出して block する
- visible body に persona 名 / editor 名 / trial 名 / source contract / validation / repair 方針が出る
- live generation 成功だが本文に未確認の統計・価格・法律・医療・金融・比較優位・会社実績が出る

停止時は `C:\tetie\WORKLOG.md` に short stop report を追記する:

- attempt id
- command / route
- result
- reason code
- relevant log paths
- suspected owner
- no code changes made, or changed files if any

### Narrow self-fix allowed

次だけは最大3回まで自己修正してよい。

- live 実行用の request payload 作成ミス
- UI 選択ミス
- test fixture / smoke script だけの誤り
- log parsing command の誤り

runtime / UI 本体を直す必要がある場合は、原則停止して報告する。別途 implementation phase として切る。

## 成功時の記録

成功したら `C:\tetie\WORKLOG.md` に追記する。

記録内容:

- attempt id
- live case
- success / runtime_reason_code
- output_guard_blocked
- quality warnings
- source grounding diagnostics
- visible body quick review
- residual risk
- live generation completed

## 完了条件

- Case 1 の live generation が実行された、または実行不可理由が明確に記録された。
- 実行された場合、logs と visible output が確認された。
- `prompt_only` が `daily_story` に閉じ、`web` / omakase に流れていない。
- 未確認 claim と internal-term leakage がない。
- WORKLOG に結果が記録された。
- final report に AGENTS / WORKLOG 更新要否を含める。

