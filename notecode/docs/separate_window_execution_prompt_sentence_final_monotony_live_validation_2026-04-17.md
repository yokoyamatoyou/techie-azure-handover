# separate window execution prompt sentence final monotony live validation 2026-04-17

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\separate_window_management_memo_deepresearch_reflection_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_priority_revision_after_deepresearch_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_instruction_window_relocation_prompt_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_instruction_first_request_sentence_final_monotony_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_triage_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_triage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_pipeline_acceptance_2026-04-17.md
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line の live validation / keep judgment だけを行う
- 実装済み diff は
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
  に閉じている前提で扱う
- production code は追加で編集しない
- AGENTS / WORKLOG / current package docs は更新しない
- current source-of-truth は上書きしない
- 目的は `keep / rollback / needs-more-work` を visible output と telemetry で判断すること

current keep-state:
- route default:
  - `grounded generic default`
- planning:
  - `opt-in only`
- structural baseline:
  - `single-pass + optional single repair 1回`
- blank company intro keep line:
  - `prompt_builder.py` の `current-business-first keep line`
- `reference realization policy`:
  - separate evidence line のまま keep
  - 今回の main line にはしない

実装済み narrow change:
- `_local_monotony_patch_scope_enabled()` を追加
- `_run_optional_repair()` を更新
- `ending_bucket_monotony` 単独 patch のときだけ local monotony scope fallback を許可
- mixed issue types には広げない
- telemetry に `scope_acceptance_path` を追加
  - `flagged_scope`
  - `local_monotony_scope`
  - `local_patch_scope`
- `effective_scope_preserved = true` なのに `scope_rejection_reason = flagged_scope_drift` を残さない

実装レポートで確認済みのこと:
- owner-local tests は pass
- `patch_path_used = true -> repair_applied = true` を focused test で確認済み
- company intro monotony guard は focused tests 上で維持
- current owner 外 failure:
  - `test_st08b4_industry_analysis_title_and_lead_do_not_echo_prompt`
  - この line の diff 起因とは判断しない

目的:
- unit/focused test pass を live-like visible improvement に接続できるか確認する
- `explanatory_article` の monotony case で repair acceptance が実際に通るかを見る
- company intro の guard が visible regression なく維持されるかを見る
- current diff を keep するか、rollback するか、追加 triage が要るかを docs-only で判断する

絶対条件:
- production code edit 禁止
- test file edit 禁止
- current package docs 更新禁止
- AGENTS / WORKLOG 更新禁止
- `reference realization policy` を今回の main line に戻さない
- `quality_guard.py` / `prompt_builder.py` / formatter / route default を触らない
- metrics だけで勝敗を決めず、visible text を必ず読む

今回やること:
1. latest artifact を確認する
   - `C:\tetie\notecode\logs\latest_generation_output.txt`
   - `C:\tetie\notecode\logs\latest_generation_output.json`
   - `C:\tetie\notecode\logs\latest_generation_quality_report.json`
2. current branch state で live validation を実施する
3. target / guard case ごとに
   - visible text
   - repair telemetry
   - rejection or acceptance path
   を保存する
4. validation note を docs に 1 本作る
5. 最後に `KEEP / ROLLBACK / NEEDS_MORE_WORK` の 3択で結論を出す

validation case design:
- case A:
  - main target
  - `explanatory_article`
  - live-like monotony case
  - 目的:
    - `patch_path_used = true`
    - `repair_applied = true`
    - `scope_acceptance_path = local_monotony_scope`
    - visible monotony 改善
- case B:
  - guard
  - `branding / company_introduction`
  - 目的:
    - monotony guard 維持
    - heading order / must-cover / title / lead / hashtags の drift なし
    - unintended broad rewrite なし
- case C:
  - optional additional guard
  - `announcement` または patch path を使わない short case
  - 目的:
    - patch-path-off line に副作用がないことをざっくり確認
  - 時間が足りなければ skip 可

judge points for each case:
- visible text:
  - 同じ文末が塊で続く感じが減ったか
  - 段落や見出しの流れが崩れていないか
  - タイトル / lead / hashtags が変な drift をしていないか
  - 読み味が patch 的な継ぎはぎになっていないか
- telemetry:
  - `patch_path_used`
  - `repair_applied`
  - `flagged_issue_types`
  - `scope_acceptance_path`
  - `scope_rejection_reason`
  - `ending_bucket_max_run`
  - `ending_bucket_monotony_score`
  - `repair_trigger_score`
- guard:
  - company intro で `shadow_section_drift` や heading drift を reopen していないか
  - mixed issue でも `local_monotony_scope` を誤適用していないか

minimum keep rule:
- case A で
  - `patch_path_used = true`
  - `repair_applied = true`
  - `scope_acceptance_path = local_monotony_scope`
  - visible monotony 改善あり
  - heading / lead / hashtags drift なし
- case B で
  - visible regression なし
  - company intro monotony guard を壊していない
- repo-wide known unrelated failure 以外に、この diff 起因の shared-check regression が見つからない

rollback rule:
- case A で live-like 実行でも `flagged_scope_drift` のまま止まり、focused test との乖離を説明できない
- case B で company intro が broad rewrite / heading drift / must-cover drop を起こす
- `local_monotony_scope` が mixed issue でも広く通ってしまう兆候が出る
- visible improvement がなく、telemetry だけ改善した形になる

needs-more-work rule:
- target case で acceptance は通るが visible text が弱い
- target case が再現しきれず、追加 triage が必要
- known unrelated failure と current diff の境界が曖昧

allowed touched files:
- logs generated by validation run
- docs note 1本

do not touch:
- production code
- tests
- AGENTS
- WORKLOG
- current planning package docs

推奨出力ファイル:
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_validation_note_2026-04-17.md`

停止条件:
- live validation のために production code edit が必要になった
- target case の再現条件が docs-only では定まらない
- `reference realization policy` や formatter line に論点が逸れた
- current diff の keep/rollback 判定より先に別 owner を触りたくなった

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施した validation case
3. case ごとの visible summary
4. case ごとの telemetry summary
5. `scope_acceptance_path` がどう出たか
6. `flagged_scope_drift` が消えたか残ったか
7. company intro の guard が維持されたか
8. `KEEP / ROLLBACK / NEEDS_MORE_WORK` の結論
9. 次に source-of-truth update prompt を作るべきか、もう 1 本 implementation prompt が必要か
10. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
