# current mainline tomorrow first prompt

更新日: 2026-04-06  
用途: 2026-04-07 の separate window で `visible_output_integrity_2026-04-06` package を current baseline から安全に開始するための prompt

## copy-paste prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode_current_mainline_handoff_2026-04-06.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\TASK.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\ROLLBACK.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\EXECUTION_PROMPT.md
- C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-07.md
- C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md

今回の実施範囲:
- current package objective は `keep core, enforce visible output integrity`
- pre-2026-04-02 records は archive-only に留める
- current success path を壊さない
- 明日の実装は Phase 01 `output_formatter.py` owner のみ
- malformed title の reproduction test と fallback trim だけを行う
- Phase 01 完了前に Phase 02 へ進まない

source-of-truth priority:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md
4. C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\TASK.md
5. C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md
6. C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\ROLLBACK.md
7. C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\EXECUTION_PROMPT.md
8. C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-07.md
9. C:\tetie\notecode_current_mainline_handoff_2026-04-06.md
10. C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md
11. C:\tetie\notecode\ALGORITHM.md
12. C:\tetie\WORKLOG.md

開始時に必ず読む artifact:
1. C:\tetie\notecode\logs\latest_generation_output.txt
2. C:\tetie\notecode\logs\latest_generation_output.json
3. C:\tetie\notecode\logs\latest_generation_quality_report.json
4. attempt id `gen-61a76943`

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

current visible baseline:
- red symptom:
  - `生成AI投資では、まずROIの説明が求められるをそろえて迷いを減らす実務の見方`
- yellow metrics:
  - `must_cover_reflection_rate=0.6667`
  - `source_grounding_reflection_ratio=0.8333`
  - `ending_bucket_monotony_score=0.8182`
  - `flat_zone_count=6`
  - `soft_warning_count=1`

明日の実行順:
1. latest malformed title の再現経路を focused test で固定する
2. `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py` の `_resolve_output_title()` / `_compact_title()` / weak-title fallback を読む
3. stitched explanatory fallback を trim する
4. weak title / empty topic path を fail-closed か compact seed に寄せる
5. owner-local test を実行する
6. shared checks を実行する
7. 通ったら docs を更新して停止する

owner-local / shared checks:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_runner.py -q

do-not:
- `output_guard.py` を同時に触らない
- `note_writer_app.py` を同時に触らない
- prompt accretion で押し切らない
- 英語の AI-ism 禁止語辞書をそのまま持ち込まない
- pre-2026-04-02 records を current planning surface に戻さない
- planner / generator core を触らない

stop:
- malformed title の再現固定ができない
- current success path regression が出る
- rollback が owner-local diff に閉じない
- `output_guard.py` を触らないと前進しないと判明する

最終報告で必ず示すこと:
- 読んだ正本ファイル
- 読んだ artifact
- current success path
- touched owner file
- 実施した変更
- 実行した tests
- rollback の有無
- Phase 02 に進まなかった理由、または進む必要がある理由
- AGENTS / WORKLOG 更新の有無
```
