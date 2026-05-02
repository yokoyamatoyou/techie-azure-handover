# current mainline tomorrow first prompt 2026-04-12

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\notecode\docs\autonomous_naturalness_repair_plan_2026-04-11.md
- C:\tetie\notecode\docs\skeleton_role_revision_proposal_2026-04-11.md
- C:\tetie\notecode\docs\separate_window_evaluate_external_research_2026-04-12.md
- C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md

開始時に必ず確認する artifact:
- C:\tetie\notecode\logs\latest_generation_output.txt
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\latest_generation_quality_report.json
- latest attempt id は 2026-04-11 09:47:38 の `gen-f914d30e`
- compare artifact:
  - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-155752-fixed3-loop1-company-intro-brief-self-reference\combined_summary.json
  - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-225911-fixed3-cycle3-root-fix-section-acceptance\combined_summary.json
  - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-233627-fixed3-cycle4-root-fix-company-intro-route-exclusion\combined_summary.json

今回の mission:
- `company_introduction` を planning/skeleton default から守るのではなく、`grounded generic-like mainline` を default に寄せるべきかを narrow diff で実装検証する
- current package objective `keep core, recover visible naturalness` は維持する
- current success path
  - C:\tetie\notecode\note\current_mainline_runner.py
  - -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  を壊さない
- `company_introduction` に限って、generic winner path を actual route decision に反映できるかを見る
- prompt accretion 禁止
- module accretion 禁止
- broad rewrite 禁止

今回の bottom line:
- external research review の判定は `REVISE_PLAN_AND_EXECUTION_ORDER`
- `company_introduction` は current evidence 上、planning/skeleton optimization の default 対象としては弱い
- local cycle 4 では `ui-short-branding-company-grounded` の winner が `generic`
- current next action は repair/fail-closed 先行ではなく、route selection を first diff で狭く切る

fixed operational rules:
- `1 diff = 1 narrow hypothesis = 1 owner scope = 1 rollback unit`
- owner は最初の実験では `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` のみに閉じる
- `company_introduction` 以外の genre の route は初手で触らない
- completed / frozen / archive-only boundary を破らない
- same hypothesis unchanged retry は 3 回まで
- keep / rollback / simplify のいずれかを明示する

今回の hypothesis:
- `company_introduction` は compact-plan を単に suppress するだけでは足りず、`actual generic grounded winner path` へ dispatch すると visible quality と must-cover 安定性が出る
- route decision は genre 名 hard-code だけではなく、task feature を使って narrow に切る
- ただし初回 diff は company-introduction を主対象とする small gate でよい

今回の owner:
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`

今回の first diff:
- route selector に `company_introduction` 向け bypass gate を 1 箇所追加する
- 重要:
  - `algorithm から compact_plan を抜く` だけにしない
  - `generic-like grounded mainline` へ本当に dispatch する
  - bypass 時は planner 専用 handoff を通さない
  - telemetry には chosen route と bypass reason だけを残す

初回 gate の方針:
- company-introduction 系で、facts / must-cover / discourse-role diversity が低いときは generic-like route
- high-density / multi-section / role-diverse な条件だけ planning route へ escalation
- threshold は fixed law として埋め込まず、compare artifact で説明できる工学的初期値に留める

do:
- `pipeline.py` 内で pre-generation route select を読む
- current `generic` winner path がどこかをコードと artifact で特定する
- `company_introduction` 用 bypass を actual dispatch に繋ぐ
- bypass reason code を narrow に追加する
- owner-local tests
- shared checks
- fixed3 compare を再実行する

do not:
- `simple_note_pipeline/pipeline.py` を同時に触らない
- `simple_note_pipeline/prompt_builder.py` を同時に触らない
- `input_contract.py` を同時に触らない
- `natural_blog_core.py` を同時に触らない
- prompt-only 改善へ逃げない
- branding 専用 branch accretion を足さない
- plan docs を diff 前に広く書き換えない

必ず確認する local evidence:
- cycle 1:
  - visible skeleton reduction first -> reject
- cycle 2:
  - hidden schema addition -> reject
- cycle 3:
  - section acceptance root fix -> reject, actuation false
- cycle 4:
  - company_intro route exclusion -> reject, generic 勝ち
- current interpretation:
  - `company_introduction` を skeleton optimization で勝たせる根拠は弱い
  - next clean experiment は `generic winner path への actual dispatch`

evaluation battery:
- production-like latest blank prompt
- `ui-short-branding-company-grounded`
- `ui-short-branding-trust`
- guard: `ui-short-case-study-explain`
- compare modes:
  - `generic`
  - `algorithm step-optimized`
  - `prompt-only persona`

今回の pass condition:
- `ui-short-branding-company-grounded` で `algorithm step-optimized` が少なくとも current `generic` 同等
- `must_cover_reflection_rate` を current generic winner より落とさない
- `source_trace_coverage` を current generic winner より落とさない
- guard regression なし
- `company_introduction` 以外に route leak がない
- visible quality が少なくとも悪化しない

今回の rollback condition:
- `company_introduction` で `must_cover_reflection_rate` が current generic winner を下回る
- `source_trace_coverage` が current generic winner を下回る
- fixed3 の non-target case に regression
- bypass したのに actual generic winner path へ入っていない
- owner scope が `pipeline.py` を超えないと成立しない

tests:
- owner-local:
  - route selector と chosen route telemetry の既存 test を探し、必要なら narrow に追加する
- shared checks:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q

もし first diff が keep になった場合の次 action:
- その時点で初めて plan docs revision proposal を作る
- 更新対象:
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- revision 内容:
  - `company_introduction` default route を grounded generic-like mainline へ寄せる
  - planning は conditional escalation として残す
  - execution order の first owner を `newalgorithm_pipeline/pipeline.py` に更新する

最終報告で必ず示すこと:
- 読んだ正本ファイル
- 読んだ compare artifact
- current success path
- touched owner file
- bypass rule の内容
- `generic / algorithm / prompt-only` の比較結果
- 実行した tests
- keep / rollback / simplify の判定
- plan docs revision の要否
- AGENTS / WORKLOG 更新の有無
```
