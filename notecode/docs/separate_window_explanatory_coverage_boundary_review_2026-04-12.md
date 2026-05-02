# separate window explanatory coverage boundary review 2026-04-12

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
- C:\tetie\notecode\docs\management_window_route_policy_coordinator_2026-04-12.md
- C:\tetie\notecode\docs\separate_window_pipeline_gate_calibration_2026-04-12.md
- C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md

開始時に必ず確認する artifact:
- planning gate closeout:
  - C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-215007-fivecase-live-pipeline\combined_report.md
  - C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-215007-fivecase-live-pipeline\combined_report.json
- explanatory target artifacts:
  - C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-215007-fivecase-live-pipeline\algorithm\bl-explanatory-misread-metric.json
  - C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-215007-fivecase-live-pipeline\generic\bl-explanatory-misread-metric.json
  - C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-215007-fivecase-live-pipeline\prompt_only\bl-explanatory-misread-metric.json
- guard reference:
  - C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-215007-fivecase-live-pipeline\algorithm\ui-short-case-study-explain.json
- current baseline:
  - C:\tetie\notecode\logs\latest_generation_output.json
  - C:\tetie\notecode\logs\latest_generation_quality_report.json

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

今回の役割:
- あなたは coverage-first boundary reviewer です
- 新しい実装はしません
- 目的は、`bl-explanatory-misread-metric` の refusal を
  - gate strictness の残り問題
  - source coverage / grounding readiness の問題
  - owner が `pipeline.py` ではない upstream 問題
  のどれとして切るべきかを narrow に判定することです

current keep state:
- `planning_opt_in_v1` の composite gate は keep
- `company / announcement / daily` は refusal 寄りの current interpretation を維持する
- `ui-short-case-study-explain` は `dense_grounding_composite` で opt-in できている
- 次に同じ gate 緩和ラインを続けない

今回の narrow question:
- `bl-explanatory-misread-metric` が `grounded_sections_insufficient` で止まったのは、
  - 実際に source-backed section density が足りないからか
  - 既存 source はあるが `pipeline.py` の coverage-first 判定が粗いからか
  - そもそも next owner が `pipeline.py` ではないからか
- 次の 1 step は code diff か、docs-only closeout か、別 owner への reroute か

hard rule:
- code edit しない
- tests を直さない
- prompt accretion 禁止
- article-type fixed routing table 禁止
- `planning_opt_in_v1` をさらに緩める前提で入らない
- multiple owner simultaneous edit を提案しない

今回の do:
- `combined_report.md/json` から explanatory case と guard case の gate telemetry を読む
- `bl-explanatory-misread-metric` の algorithm / generic / prompt_only artifact を比較する
- explanatory case の
  - grounded section count / ratio
  - must-cover reflection
  - source trace coverage
  - source grounding item の有無
  - article-type prior
  を整理する
- 「source が薄いのか」「source はあるが route entry 判定が粗いのか」を切り分ける
- 次の owner を 1 つに閉じられるか判断する

今回の do not:
- `daily` の旧 loop を reopen しない
- case-study を default route の根拠にしない
- `company / announcement` を reopen しない
- 大きい remediation plan を書かない

判定カテゴリ:
- `NO_CODE_CLOSEOUT_KEEP_GATE`
- `PIPELINE_NARROW_DIFF_NEXT`
- `UPSTREAM_SOURCE_READINESS_NEXT`
- `DOCS_ONLY_REROUTE`

判定の考え方:
- `NO_CODE_CLOSEOUT_KEEP_GATE`:
  - explanatory case は source coverage が足りず、今は code diff を打つより current refusal を keep するほうが安全
- `PIPELINE_NARROW_DIFF_NEXT`:
  - existing source-backed material はあるのに、`pipeline.py` の coverage-first 判定が粗くて explanatory case を拾えていない
- `UPSTREAM_SOURCE_READINESS_NEXT`:
  - `pipeline.py` より upstream の source organization / section grounding preparation が先
- `DOCS_ONLY_REROUTE`:
  - evidence は足りるが次 owner がまだ 1 file に閉じず、まず docs で boundary を切り直すべき

期待する出力:
1. 読んだ正本ファイル
2. 読んだ artifact
3. `bl-explanatory-misread-metric` の refusal 理由の整理
4. `ui-short-case-study-explain` と何が違うか
5. next owner を `pipeline.py` に閉じられるか
6. 判定カテゴリ
7. 判定理由
8. もし next code diff を出すなら:
   - owner 1 file
   - narrow hypothesis
   - pass / rollback / stop 条件
9. AGENTS / WORKLOG / plan docs / code を触っていないこと

最終的に欲しい答え:
- technical explain の残課題は gate strictness の継続調整か、別問題か
- 次の 1 owner はどこか
- それとも今は code diff を出さず closeout すべきか
```
