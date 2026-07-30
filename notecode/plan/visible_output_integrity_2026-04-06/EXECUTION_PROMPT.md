# visible_output_integrity_2026-04-06 EXECUTION PROMPT

## next startup use

- 次回起動時は、このファイル内の `prompt` ブロックをそのまま使う
- 2026-04-07 の separate window 開始では `C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-07.md` を優先してよい
- current planning source-of-truth は `visible_output_integrity_2026-04-06` package に固定する
- pre-2026-04-02 records は archive snapshot 経由でのみ参照する
- `output_surface_reduction_2026-04-06` / `orchestration_surface_reduction_2026-04-06` は completed reference として扱う
- `architecture_target_refactor_2026-04-06` は frozen reference として扱う

## prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\TASK.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\ROLLBACK.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\EXECUTION_PROMPT.md
- C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md

今回の実施範囲:
- current package objective は `keep core, enforce visible output integrity`
- pre-2026-04-02 records は archive-only に留める
- current success path を壊さない
- Phase 01 `output_formatter.py` owner だけを初手で触る
- Phase 02 以降は Phase 01 の結果で必要な場合だけ進む

source-of-truth priority:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md
4. C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\TASK.md
5. C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md
6. C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\ROLLBACK.md
7. C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\EXECUTION_PROMPT.md
8. C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md
9. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md
10. C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md
11. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
12. C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
13. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
14. C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md
15. C:\tetie\notecode\ALGORITHM.md
16. C:\tetie\WORKLOG.md

開始時に必ず確認する artifact:
1. C:\tetie\notecode\logs\latest_generation_output.txt
2. C:\tetie\notecode\logs\latest_generation_quality_report.json
3. attempt id `gen-61a76943`

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

archive-only records:
- C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\

completed reference として keep する package:
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\

frozen reference として keep する package:
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\

current phase:
- 01 Output Formatter Title Integrity Trim

Phase 01 objective:
- malformed title を作る stitched fallback を `output_formatter.py` owner だけで narrow に減らす

Phase 01 do:
- latest red title の reproduction path を focused test で固定する
- `_resolve_output_title()` -> `_compact_title()` fallback を読む
- prompt accretion ではなく title fallback trim で symptom を止める

Phase 01 do-not:
- `output_guard.py` を同時に触らない
- `note_writer_app.py` を初手で触らない
- pre-2026-04-02 records を current planning surface に戻さない
- planner / generator core を触らない

Phase 01 shared checks:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_runner.py -q

Phase 01 pass condition:
- latest malformed title shape を focused test で再現できなくなる
- current success path regression がない
- rollback が owner-local diff で説明できる

最終報告で必ず示すこと:
- 読んだ正本ファイル
- 読んだ archive snapshot
- current success path
- touched owner file
- 実施した変更
- 実行した tests
- rollback の有無
- AGENTS / WORKLOG 更新の有無
```
