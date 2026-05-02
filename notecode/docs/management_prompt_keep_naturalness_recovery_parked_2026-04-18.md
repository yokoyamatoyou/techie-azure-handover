# management prompt keep naturalness recovery parked 2026-04-18

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\management_stop_report_after_failed_pipeline_current_first_triage_2026-04-18.md
- C:\tetie\notecode\docs\parked_package_prompt_naturalness_recovery_2026-04-18.md
- C:\tetie\notecode\docs\separate_window_heading_drift_pipeline_contract_hint_consumer_triage_note_2026-04-18.md
- C:\tetie\notecode\logs\heading_drift_upstream_current_first_hint_live_validation_20260418-142418\summary.json

今回の依頼種別:
- management prompt
- `KEEP_PACKAGE_PARKED_NOT_FIXED`
- implementation prompt ではない
- source-of-truth rewrite ではない

今回の実施範囲:
- current source-of-truth と stop reports が `parked / not fixed` で整合しているか確認する
- package を reopen せずに維持するための current judgment を再確認する
- stale implementation prompt を current prompt として誤使用しないよう retire / hold を整理する
- production code / tests は編集しない
- 新しい implementation prompt は作らない

current fixed judgment:
- current package:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07`
- package state:
  - `parked / not fixed`
- current success path:
  - keep
- structural baseline:
  - `single-pass + optional single repair 1回`
- default route:
  - `grounded generic default`
- planning / skeleton:
  - opt-in only
- failed / rollback 済み / unchanged retry 禁止:
  - `prompt_builder.py` simplification-first wording line
  - `pipeline.py` current-first source ordering / hint triage
  - `pipeline.py` core_message current-first hint
- next owner:
  - not fixed
- next narrow hypothesis:
  - not fixed

why parked stays correct:
- `prompt_builder.py` も `pipeline.py` も opener drift containment を owner-local に止め切れなかった
- `source ordering` の後に `core_message` まで試しても V3 mandatory gate を越えなかった
- 同じ owner 周辺で `topic_statement` / `must_cover` / hint branch を足すと accretion が進みやすい
- 現時点で legal な `1 owner / 1 hypothesis` は source-of-truth と do-not-retry list を守る限り未確定

this window role:
- parked 維持の management confirmation
- source-of-truth の current judgment を確認する
- next implementation を出さないことを明示する
- user が後で reopen 判断しやすいよう、current block を短く整理する

this window will do:
1. current source-of-truth が `parked / not fixed` に揃っているか確認する
2. failed hypotheses と do-not-retry boundary を再確認する
3. stale implementation prompt を current prompt として使わない整理をする
4. 必要なら docs-only の parked confirmation note を 1 本作る
5. reopen には explicit user decision が必要だと明記する

this window will not do:
- production code edit
- test edit
- live validation rerun
- `prompt_builder.py` reopen
- `pipeline.py` reopen
- new implementation prompt creation
- multiple owner reopen planning
- deepresearch implementation proposal
- current package source-of-truth の broad rewrite

allowed output:
- if docs are already aligned:
  - file edit なしで management summary を返す
- if one parked confirmation note is useful:
  - docs-only で 1 note 追加
- note を作る場合の推奨 path:
  - C:\tetie\notecode\docs\management_parked_confirmation_naturalness_recovery_2026-04-18.md

required judgment points:
1. current package state
2. why parked is still the least risky choice
3. which hypotheses are explicitly retired
4. whether any legal `1 owner / 1 hypothesis` remains now
5. what kind of user decision would be required to reopen

reopen threshold:
- reopen するには user が明示的に次のどちらかを選ぶ必要がある
  - current package の do-not-retry / owner boundary を一部緩める
  - current package 外の新しい research / redesign line を切る
- explicit reopen decision がなければ parked のまま維持する

stop conditions:
- source-of-truth docs 同士が `parked` judgment で不整合
- stale prompt が current prompt として残り続ける
- parked keep に見せかけて implementation を始めたくなった

final report must include:
1. 読んだ参照ルールファイル
2. 今回の実施範囲
3. current package state
4. parked 維持が妥当な理由
5. retired / do-not-retry hypotheses
6. legal な next owner が今は未確定かどうか
7. reopen に必要な user decision
8. docs-only で何を更新したか、または更新なしだったか
9. production code / tests / AGENTS / WORKLOG を更新していないこと
```
