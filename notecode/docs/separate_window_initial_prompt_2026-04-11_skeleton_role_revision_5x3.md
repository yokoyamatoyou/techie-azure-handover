# separate window initial prompt 2026-04-11 skeleton role revision 5x3

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
- C:\tetie\notecode\docs\skeleton_role_revision_proposal_2026-04-11.md
- C:\tetie\notecode\docs\autonomous_naturalness_repair_plan_2026-04-11.md
- C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-11.md
- C:\tetie\notecode\docs\stepwise_three_article_gate_2026-04-08.md
- C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md

今回の mission:
- `skeleton_role_revision_proposal_2026-04-11.md` の方針で、骨格の配置と役割を適正化する
- 骨格は捨てない
- ただし骨格の責務を `content planning / source alignment / do_not_mix` に縮める
- visible prose は prompt-only に近い書き味へ戻す
- current accepted baseline を壊さず、`minimum hybrid` を `micro-skeleton only` に寄せる
- `fixed3` の 3 記事を毎サイクル作成・比較・評価し、修正を 5 サイクル回す

今回の根本仮説:
- 研究で優位だったのは `骨格そのもの` ではなく `内容計画の骨格`
- current notecode は骨格に prose の型まで持たせていたため、AIっぽい見え方と空節を生んでいた
- したがって次の改善軸は `prompt accretion` ではなく `planner responsibility reduction`

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

accepted baseline:
- keep state は `self_reference_policy UI/contract` と `company introduction source-aware prune`
- recent failed loops は採用しない
- 新規変更はすべて `owner-local rollback` 可能であること
- compare の accepted reference は
  - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-155752-fixed3-loop1-company-intro-brief-self-reference\combined_summary.json

必ず読む recent docs:
1. C:\tetie\notecode\docs\skeleton_role_revision_proposal_2026-04-11.md
2. C:\tetie\notecode\logs\latest_generation_output.txt
3. C:\tetie\notecode\logs\latest_generation_output.json
4. C:\tetie\notecode\logs\latest_generation_quality_report.json
5. accepted baseline compare
   - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-155752-fixed3-loop1-company-intro-brief-self-reference\combined_summary.json

評価対象の fixed3:
- ui-short-branding-trust
- ui-short-case-study-explain
- ui-short-branding-company-grounded

固定比較モード:
- generic
- algorithm
- prompt_only

今回の algorithm revision 方針:
- `role hidden / prose free`
- `no source, no standalone section`
- `no forced fixed sequence unless source supports it`
- `self_reference_policy belongs to realization, not planning`
- `micro-skeleton may merge, but should not invent`

今回の実装原則:
- planner は次だけ決める
  - 節の役割
  - 使う source fact
  - 混ぜない論点
  - merge 可能性
- planner は次を決めすぎない
  - 固定見出し順
  - 節冒頭テンプレ
  - 一人称の出し方
  - 段落の長さ
  - prose の呼吸
- writer は `prompt_raw + source fact + compact naturalness rail + micro-skeleton` を主入力にする
- editor / repair は skeleton 復元ではなく
  - source 逸脱
  - AI 的反復
  - paragraph breath の均しすぎ
  - 主語消失
  だけを優先する

禁止事項:
- prompt accretion 禁止
- module accretion 禁止
- 研究知見を理由に固定順テンプレを増やすこと禁止
- source にない節を独立見出し化すること禁止
- compat prompt を evidence/source として混ぜること禁止
- same hypothesis unchanged retry は 3 回まで
- compare を回さず keep にしない

UI 方針:
- 一人称 UI は keep 候補
- ただし planner には渡さず writer realization parameter としてだけ扱う
- `私 / 私たち / 当社 / 弊社 / なし寄り` は許容

web search 方針:
- 開始時に planning / skeleton / content planning 系の一次情報を軽く確認してよい
- ただし code change は research quote を増やすためではなく、`skeleton responsibility reduction` の narrow diff に限る
- 研究を追加確認する場合は ACL / TACL / arXiv など一次情報を優先する

5 サイクル運用:

cycle 1:
- owner 第一候補:
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- narrow hypothesis:
  - writer prompt から `固定順テンプレ` と `節冒頭テンプレ` を減らし、planner は `role / fact / do_not_mix / merge_allowed_with` に縮退させる
- focus:
  - `case_study` と `branding/company_introduction` の heading progression pressure を弱める

cycle 2:
- owner 第一候補:
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- narrow hypothesis:
  - `micro-skeleton` へ `merge_allowed_with` と `exclusive fact` 条件を入れ、source が薄い role の独立節を禁止する
- focus:
  - `result` / `condition` / `closing` の merge

cycle 3:
- owner 第一候補:
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- narrow hypothesis:
  - planner output を visible structure へ過剰投影しない gate を入れ、`role hidden / title free` を守る
- focus:
  - planner/writer boundary の整理

cycle 4:
- owner 第一候補:
  - C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
  - または `prompt_builder.py` に閉じるならそちらを優先
- narrow hypothesis:
  - `self_reference_policy` と surface micro-rails を planner から切り離し、writer realization rail に限定する
- focus:
  - 一人称と骨格責務の分離

cycle 5:
- owner 第一候補:
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - 必要なら `prompt_builder.py`
- narrow hypothesis:
  - editor / repair を `skeleton 復元` ではなく `AI-like surface repair` に限定し、skeleton の再テンプレ化を防ぐ
- focus:
  - regression を起こさず paragraph breath と反復を下げる

各 cycle で必ず行うこと:
1. 現在の accepted baseline を確認する
2. web search か既読 research から、その cycle の仮説に必要な一次情報だけ確認する
3. owner-local に実装する
4. owner-local tests
5. shared checks
6. `fixed3` live compare を回す
7. `generic / algorithm / prompt_only` を比較する
8. keep / rollback / simplify を判定する
9. 次 cycle は accepted state から開始する

各 cycle の採否ルール:
- keep 条件:
  - target case で prompt_only と同等以上、または prompt_only にない groundedness / business readiness の優位を説明できる
  - non-target regression がない
  - source_trace_coverage を落とさない
  - visible heading template 化が増えない
- reject 条件:
  - 1 case でも accepted baseline より明確に悪化
  - non-target regression
  - source coverage 低下
  - 空節の増加
- reject 時:
  - 必ず rollback
  - rejected hypothesis を unchanged で再投入しない

shared checks:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q

live compare command:
- C:\tetie\notecode\.venv\Scripts\python.exe tools\run_minimum_hybrid_compare_matrix.py --live --case-set fixed3 --label <cycle-label>

開始時に必ず確認する code location:
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - heading progress rule
  - structure lines
  - writer prompt assembly
  - planner/writer boundary
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - planner output handoff
  - repair acceptance
  - visible structure projection
- C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
  - self_reference_policy
  - prompt surface items
  - writer realization に残す micro-rails
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
  - heading progression
  - company intro prompt
  - case study prompt

実験の目的を見失わないための要点:
- 目的は骨格を消すことではない
- 目的は骨格を invisible planning layer に戻すこと
- visible prose は prompt-only に近い自然さへ戻す
- minimum hybrid の価値は
  - source grounding
  - fact allocation
  - do_not_mix
  - no hallucination
  に限定して残す

最終報告で必ず示すこと:
- 読んだ source-of-truth
- 読んだ research source
- 5 cycle 全体の accepted / rejected の一覧
- 各 cycle の owner / hypothesis / diff / tests / live compare result
- `generic / algorithm / prompt_only` の勝敗
- keep した変更
- rollback した変更
- 減らした planner responsibility
- まだ残る AI-like symptom
- 骨格の配置と役割が適正化したと言えるか
- `minimum hybrid with micro-skeleton only` を継続するか
- `prompt-only` にまだ負けているなら、どの責務をさらに剥がすべきか
- AGENTS / WORKLOG 更新の有無
```
