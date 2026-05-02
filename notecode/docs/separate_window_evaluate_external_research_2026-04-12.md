# separate window evaluate external research 2026-04-12

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
- C:\tetie\notecode\research\新しいフォルダー (10)\00_README_FIRST.md
- C:\tetie\notecode\research\新しいフォルダー (10)\02_PROJECT_AND_GOAL.md
- C:\tetie\notecode\research\新しいフォルダー (10)\03_CURRENT_ARCHITECTURE_AND_TERMS.md
- C:\tetie\notecode\research\新しいフォルダー (10)\04_EXPERIMENT_HISTORY_AND_FAILURES.md
- C:\tetie\notecode\research\新しいフォルダー (10)\05_CURRENT_EVIDENCE_AND_ARTIFACTS.md
- C:\tetie\notecode\research\新しいフォルダー (10)\06_REQUIRED_OUTPUT.md

外部AIの research 結果配置先:
- C:\tetie\notecode\research\新しいフォルダー (10)\新しいフォルダー

今回の mission:
- 外部AIの research 結果を読む
- それが current plan / current architecture / current next step を本当に更新する価値があるかを判定する
- 単なる言い換えや既知結論の再確認なら plan は修正しない
- current source-of-truth を動かす場合だけ、最小変更で plan revision proposal を作る

今回の論点は narrow:
- `company_introduction` を planning/skeleton optimization の対象として維持すべきか
- それとも `generic-like mainline` を正規ルートに寄せるべきか
- もし route selection を導入するなら、どの gating rule が妥当か

重要:
- あなたの役割は research reviewer 兼 plan gatekeeper です
- 新しい実装はしない
- まず evidence を読み、current plan を変える必要があるかを判定する
- keep / revise / reject を明示する

current known local evidence:
- cycle 1: visible skeleton reduction first -> reject
- cycle 2: hidden schema addition -> reject
- cycle 3: section acceptance root fix -> reject, actuation false
- cycle 4: company_intro route exclusion -> reject, generic 勝ち
- ここまでの local result では `company_introduction を skeleton optimization で勝たせる根拠は弱い`

読む順番:
1. current source-of-truth
   - README / TASK / PROGRESS / ROLLBACK / EXECUTION_PROMPT
2. local interpretation docs
   - skeleton_role_revision_proposal_2026-04-11.md
3. external research packet summary files
   - 00_README_FIRST.md
   - 02_PROJECT_AND_GOAL.md
   - 03_CURRENT_ARCHITECTURE_AND_TERMS.md
   - 04_EXPERIMENT_HISTORY_AND_FAILURES.md
   - 05_CURRENT_EVIDENCE_AND_ARTIFACTS.md
   - 06_REQUIRED_OUTPUT.md
4. external AI result files
   - C:\tetie\notecode\research\新しいフォルダー (10)\新しいフォルダー 内の全ファイル
5. 必要なら compare artifact
   - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-155752-fixed3-loop1-company-intro-brief-self-reference\combined_summary.json
   - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-225911-fixed3-cycle3-root-fix-section-acceptance\combined_summary.json
   - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-233627-fixed3-cycle4-root-fix-company-intro-route-exclusion\combined_summary.json

評価観点:
1. novelty
- 外部AIの research は current local conclusion に対して本当に新しい情報を足しているか
- それとも既知の「company_intro は generic-like が妥当かも」を別表現で再確認しているだけか

2. actionability
- 提案は code owner / route rule / gating rule / acceptance criteria に落とせるか
- 「もっと自然に」「もっと柔軟に」のような非実装的提案は plan revision 理由として弱い

3. fit to local evidence
- external conclusion は cycle 1-4 の reject evidence と整合しているか
- local evidence と衝突する場合、その衝突を埋める新しい一次情報や明確な条件があるか

4. complexity
- plan revision が prompt accretion / module accretion / broad rewrite を要求していないか
- `1 phase = 1 narrow hypothesis = 1 owner scope` を守れるか

5. decision power
- research を採用すると next action が narrower / clearer / safer になるか
- 逆に曖昧になるなら採用しない

判定カテゴリ:
- `KEEP_CURRENT_PLAN`
  - current plan を変えない
  - next step も変えない
- `REVISE_NEXT_STEP_ONLY`
  - package objective は変えない
  - ただし next owner / next hypothesis を変える
- `REVISE_PLAN_AND_EXECUTION_ORDER`
  - current package docs の update を提案する
  - next step だけでなく、phase interpretation も変える
- `REJECT_EXTERNAL_RESEARCH_AS_NON_ACTIONABLE`
  - research は参考になるが、現時点では current plan を動かさない

強い revision 条件:
- 外部AIが明確な route selection rule を出している
- その rule が cycle 1-4 の local failures を一段上の abstraction で説明できる
- その rule が small owner scope diff に落ちる
- current complexity / rollback discipline を壊さない

revision 不可条件:
- 外部AIが generic-like / prompt-only-like / planning route のどれを採るべきか曖昧
- code owner が複数にまたがる
- broad refactor 前提
- local failures と矛盾するのに解消根拠がない

今回の期待出力:
1. 読んだファイル一覧
2. 外部AI research の要点 3-7 行
3. current local conclusion と一致する点 / 矛盾する点
4. 判定
   - KEEP_CURRENT_PLAN / REVISE_NEXT_STEP_ONLY / REVISE_PLAN_AND_EXECUTION_ORDER / REJECT_EXTERNAL_RESEARCH_AS_NON_ACTIONABLE
5. 判定理由
6. もし修正するなら:
   - どの doc を更新すべきか
   - どういう文言に変えるべきか
   - next owner / next hypothesis / pass gate をどう変えるか
7. もし修正しないなら:
   - current next step を維持する理由
   - 外部AI research のどこが不足していたか
8. AGENTS / WORKLOG / plan docs 更新の要否

重要な姿勢:
- 外部AIの conclusion を鵜呑みにしない
- local experiments 4 回分の reject evidence を優先する
- ただし research がそれをより高いレベルで整理し、next step を narrow にできるなら採用してよい
- plan を動かすのは `evidence that changes action` があるときだけ
```
