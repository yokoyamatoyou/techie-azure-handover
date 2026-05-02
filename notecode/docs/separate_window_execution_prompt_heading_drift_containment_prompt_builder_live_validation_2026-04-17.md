# separate window execution prompt heading drift containment prompt builder live validation 2026-04-17

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\separate_window_instruction_handoff_heading_drift_containment_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_heading_drift_containment_management_planning_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_triage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_containment_prompt_builder_implementation_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_visible_smoke_after_rollback_note_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\summary.json
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py

今回の依頼種別:
- live validation / compare prompt
- `HEADING_DRIFT_CONTAINMENT_FIRST` line の first implementation visible validation
- source-of-truth update ではない
- implementation prompt ではない
- deepresearch prompt ではない

今回の実施範囲:
- `prompt_builder.py` owner の `TITLE_LEAD_HEADING_CONTRACT_FIRST` 実装について、visible output と secondary telemetry を使って keep candidate かどうかを判断する
- production code / tests は追加で編集しない
- AGENTS / WORKLOG / current package docs は更新しない
- generated logs と validation note だけを追加する
- 目的は `KEEP_CANDIDATE / NEEDS_MORE_WORK / REGRESSION` の 3択で次の line を決めること

current inherited implementation result:
- touched owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- implemented hypothesis:
  - title / lead / 最初の見出し / 1節目本文を同一 frame に縛る短い contract cluster を generation prompt に追加した
- exact local change read:
  - generic contract line:
    - `title・lead・最初の見出しは同じ論点を別役割でつなぐ。`
  - generic structure line:
    - `leadから最初の見出し、1節目本文までを同じフレームでつなぎ...`
  - blank company intro line:
    - `title・lead・最初の見出し・1節目本文はまず current business が見える流れにそろえ...`
- already confirmed in tests:
  - focused owner-local pass
  - full simple-note pass
  - simple-note quality guard pass
- not yet confirmed:
  - live visible gain
  - non-target visible regression absence

current keep-state:
- route default:
  - `grounded generic default`
- planning:
  - `opt-in only`
- structural baseline:
  - `single-pass + optional single repair 1回`
- current redirect line:
  - `HEADING_DRIFT_CONTAINMENT_FIRST`
- first owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- do not reopen:
  - `pipeline.py`
  - `quality_guard.py`
  - `SECTION_SHADOW` company intro 再導入
  - repair acceptance reopen
  - `sentence-final monotony` continuation

core validation question:
- この contract cluster は、実際の生成結果で
  - title drift
  - lead drift
  - heading wording / heading sequence drift
  - company intro first heading の history-first reanchor
  を visible に抑えるか
- それとも prompt text 上は良くても、実文では
  - 意味的重複
  - 言い換え反復
  - hard / stiff な読み味
  - non-target regression
  が出るか

重要:
- metrics だけで判断しない
- generated visible text を必ず読む
- 今回の主判定は
  - AIっぽさが減ったか
  - 意味的重複が減ったか
  - 読みやすさが上がったか
  を human-visible 基準で見ること

validation case set:
- case V1:
  - latest adaptive explanatory baseline rerun
  - source:
    - `C:\tetie\notecode\logs\latest_generation_output.json`
  - role:
    - explanatory target
- case V2:
  - saved adaptive explanatory replay
  - source:
    - `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
  - role:
    - explanatory target fallback
- case V3:
  - company intro guard
  - source:
    - `C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json`
  - role:
    - main target company intro
- case G1:
  - non-target branding guard
  - source:
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\20260322-123339-short\ui-short-branding-trust.json`
  - role:
    - off-target regression guard

execution path:
- current success path に固定する
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

self-execution policy:
1. まず local context だけで case rerun / replay の実行方法を確定する
2. current branch state で cases を実行する
3. generated artifact を保存する
4. visible text を読み、secondary telemetry を整理する
5. blocking error が出たら local self-fix を先に行う
6. local self-fix だけで解けない blocker に限り、WEB検索を1回だけ行ってよい
7. WEB検索は official docs / primary sources を優先し、production判断の主根拠を web に置き換えない
8. WEB検索後も validation 実行ができなければ、その時点で user report を作って停止する
9. blocker がなければ、最後まで自律的に compare / note 作成 / judgment まで進む

what to record for each case:
- visible summary:
  - title が lead / 最初の見出しと同じ論点で自然につながるか
  - ただし同じ言い換え反復にはなっていないか
  - 最初の見出しと1節目本文が同じ frame で始まるか
  - explanatory で説明カード調や継ぎはぎ感が減ったか
  - company intro で current business から入れているか
  - history-first drift が止まっているか
  - 読みやすさが上がったか、硬くなっていないか
  - 意味役割の分離
    - title = 論点
    - lead = 読む軸
    - first heading = 最初に進む観点
    - first section = 見出しの具体化
    が見えるか
- secondary telemetry:
  - `repair_entry.repair_required`
  - `repair_entry.flagged_issue_types`
  - `repair_call.patch_path_used`
  - `repair_applied`
  - `scope_acceptance_path`
  - `scope_rejection_reason`
  - title / lead / hashtags / heading sequence の変化有無

minimum keep rule:
- V1 / V2 explanatory の少なくとも一方で
  - title / lead / first heading の drift が前より明確に減る
  - 同じ論点の反復だけに見えない
  - explanatory として main candidate に近づく visible 改善がある
- V3 company intro で
  - current-business-first read を保てる
  - first heading の history-first drift を抑えられる
  - current-first keep line を visible に壊していない
- G1 guard で
  - 明確な regression がない

regression rule:
- V1 / V2 で title / lead / first heading がむしろ硬く同語反復になる
- V3 で current-business-first が壊れる、または history-first が残る
- G1 で non-target regression が visible に出る
- prompt text は整っていても、実文で AIっぽい説明カード感や意味的重複が増える

needs-more-work rule:
- drift は少し減るが main candidate と言える visible quality に届かない
- company intro と explanatory で勝ち負けが割れる
- regression はないが gain も弱い
- compare 結果から second lever か narrower re-implementation が必要と読める

what not to do:
- production code edit
- test edit
- source-of-truth update
- current package docs 更新
- AGENTS / WORKLOG 更新
- `pipeline.py` / `quality_guard.py` reopen
- metrics だけで勝敗を決める
- deepresearch へ逃がす

allowed touched files:
- generated logs only
- validation note 1本

recommended artifact dir:
- `C:\tetie\notecode\logs\heading_drift_containment_prompt_builder_live_validation_<timestamp>\`

recommended output file:
- `C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_live_validation_note_2026-04-17.md`

stopping conditions:
- validation 実行のために production code edit が必要になった
- case replay / rerun の入口が local context だけでは確定しない
- current branch state で representative cases を再現できない
- local self-fix + 1回のWEB検索後も blocker が解消しない
- compare ではなく別 implementation を始めたくなった

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施した validation cases
3. 実行したコマンド
4. case ごとの visible summary
5. case ごとの secondary telemetry summary
6. explanatory target が main candidate に近づいたか
7. company intro が current-business-first を保てたか
8. non-target guard に regression がないか
9. `KEEP_CANDIDATE / NEEDS_MORE_WORK / REGRESSION` の結論
10. 次が source-of-truth update prompt か、next implementation / triage prompt か
11. WEB検索を使ったかどうか
12. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
