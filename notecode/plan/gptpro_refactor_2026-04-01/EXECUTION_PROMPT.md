# gptpro_refactor_2026-04-01 EXECUTION PROMPT

## prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\GPTPRO.txt
- C:\tetie\notecode_current_mainline_handoff_2026-03-31.md
- C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\README.md
- C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\TASK.md
- C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\PROGRESS.md
- C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\ROLLBACK.md
- C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\EXECUTION_PROMPT.md

今回の実施範囲:
- gptpro_refactor_2026-04-01 package の stopped state から再開する
- current success path を壊さない
- model は未定のままにする
- narrow 粒度を維持する
- 1 phase = 1 narrow hypothesis = 1 owner scope を崩さない
- phase / retry-stop / rollback rule を守る
- completion gate を満たせるところまで進める

source-of-truth priority:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\README.md
4. C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\TASK.md
5. C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\PROGRESS.md
6. C:\tetie\notecode\ALGORITHM.md
7. C:\tetie\WORKLOG.md
8. C:\tetie\notecode\GPTPRO.txt

開始時に必ず読むファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\WORKLOG.md
5. C:\tetie\notecode\GPTPRO.txt
6. C:\tetie\notecode_current_mainline_handoff_2026-03-31.md
7. C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\README.md
8. C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\TASK.md
9. C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\PROGRESS.md
10. C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\ROLLBACK.md
11. C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\EXECUTION_PROMPT.md

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

keep する current kept state:
- C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
  - compare axis normalization fix
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - compare opener / ranking soften
- C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py
  - tool-compare abswinner narrow fix
- C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py
  - compare repeated ending diversification の安全版

current stopped state:
- package:
  - C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\
- current phase:
  - Phase 07 Sentinel Sweep
- status:
  - stopped
- reason:
  - initial sentinel fail の `bl-announcement-spec-change` は `newalgorithm_pipeline/pipeline.py` owner の narrow fix で解消済み
  - rerun 後に残った residual は `bl-branding-values-stance` の title prompt echo
  - 次 diff は `output_formatter.py` owner へ移るため、同一 Phase 07 内で続行すると `1 phase = 1 owner scope` に反する

直近の live artifact:
- initial sentinel:
  - C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260402-gptpro-phase07-sentinel
- rerun after announcement fix:
  - C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260402-gptpro-phase07-sentinel-rerun-01
- residual fail:
  - bl-branding-values-stance
- visible residual:
  - title prompt echo:
    - 機能の多さより、現場で迷わない設計を重視する会社の姿勢紹介記事。

直近の code change:
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - announcement target section の prompt echo sentence を role-aligned sentence に置換する final-body stabilizer を追加済み
- C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py
  - announcement prompt echo stabilizer test を追加済み

直近で通っている checks:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st07g6aa or st07g6a or st07g0 or st07g0a or st07h or st07e or st07g" -q
  - 22 passed
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase01_contract.py -q
  - 24 passed
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q
  - 42 passed
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q
  - 9 passed
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q
  - 77 passed

do-not:
- prompt accretion をしない
- rollback 不可能な大改修をしない
- 1 phase で複数 mechanism を触らない
- failed hypothesis をそのまま再投入しない
- human_resonance* を初手で触らない
- current success path を壊さない
- prompt echo detector threshold 調整で逃げない
- output formatter 止血を compare residual に流用しない

再開時の最初の判断:
1. `PROGRESS.md` と `ROLLBACK.md` の stopped state を確認する
2. 同一 Phase 07 をそのまま続行しない
3. branding title echo residual を扱うなら、package rule を崩さない形で new narrow slice を先に明文化する
4. new narrow slice を切る場合は owner を 1 つに閉じる
   - 最有力 owner:
     - C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py
5. package docs 更新なしで owner を跨ぐ必要があるなら停止して user report する

推奨再開手順:
1. `README.md / TASK.md / PROGRESS.md / ROLLBACK.md` を読み、Phase 07 stopped の妥当性を確認する
2. branding title echo residual を new narrow slice として扱えるなら、package docs を最小更新して owner scope を `output_formatter.py` に切り直す
3. `bl-branding-values-stance` の title prompt echo だけを対象に narrow fix する
4. owner-local tests を追加または更新する
5. shared checks を通す
6. live rerun:
   - C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\tools\run_current_mainline_genre_sweep.py --phase genre-rerun --live --genres branding,announcement,case_study,comparative_review --artifact-dir <new artifact dir>
7. Phase 07 が pass したら `PROGRESS.md` を Phase 08 へ進める
8. Phase 08 では fixed 3 cases の final visual loop を最大 4 ループまで回す

shared check commands:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q

Phase 08 final fixed 3 cases:
- st-comparative-cross-department
- ui-short-announcement-dense-must-cover
- ui-short-case-study-explain

Phase 08 final loop command:
- C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\tools\run_current_mainline_genre_sweep.py --phase genre-rerun --live --case-ids st-comparative-cross-department,ui-short-announcement-dense-must-cover,ui-short-case-study-explain --artifact-dir <new artifact dir>

停止条件:
- 同一 phase で 3 回自己修正しても gate を越えられない
- current success path regression
- rollback 不可能な diff が必要
- failed hypothesis の unchanged 再投入が必要
- package rule を崩さないと次 diff に進めない

最終報告で必ず示すこと:
- 読んだ正本ファイル
- current success path
- keep した修正
- 作成した package path
- 各 phase の pass / fail
- rollback の有無
- final visual loop の結果
- AGENTS / WORKLOG 更新の有無
```
