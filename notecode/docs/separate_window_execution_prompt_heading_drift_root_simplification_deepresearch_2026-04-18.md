# separate window execution prompt heading drift root simplification deepresearch 2026-04-18

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
- C:\tetie\notecode\docs\separate_window_management_memo_deepresearch_reflection_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_priority_revision_after_deepresearch_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_targeted_deepresearch_redirect_after_sentence_final_stop_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_heading_drift_containment_management_planning_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_triage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_live_validation_note_2026-04-17.md
- C:\tetie\notecode\logs\heading_drift_containment_prompt_builder_live_validation_20260418-001250\summary.json
- C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\summary.json
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py

今回の依頼種別:
- targeted deepresearch prompt
- `HEADING_DRIFT_CONTAINMENT_FIRST` line の root simplification research
- source-of-truth update ではない
- implementation prompt ではない
- compare prompt ではない

今回の実施範囲:
- local docs / logs / code read と external deepresearch を組み合わせて、
  `heading drift containment` をこのまま owner-local rules の積み増しで進めるべきか、
  それとも simpler root layer へ戻すべきかを narrow に判断する
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない
- docs note 1本だけを作る

current problem framing:
- `2026-04-18 JST` live validation で verdict は `REGRESSION`
- exact read:
  - V1 explanatory:
    - partial gain
  - V2 explanatory:
    - gain weak
  - V3 company intro:
    - first heading / first section が history-first に再アンカー
    - current-business-first keep line を維持できない
  - G1 non-target branding:
    - clear regression なし
- local concern:
  - same owner `prompt_builder.py` 内で contract lines を足していくと、
    category-specific patchwork が増え、根本原因の切り分けが難しくなる
  - current package docs でも
    - `prompt accretion` 禁止
    - `hidden reviser accretion` 禁止
    - historical loop を future default にしない
    が明示されている

must inherit from local evidence:
- `prompt accretion` ではなく runtime owner / state flow を整えるのが package objective
- prompt-only は floor であり、strongest baseline / best practice ではない
- skeleton / planning default は勝ち筋を示していない
- `skeleton responsibility too wide` の failure memory がある
- current validation では generic contract line が explanatory を少し改善しても、
  company intro では current-business-first keep を守れていない

core research question:
- 今の failure は `prompt_builder.py` の局所 wording 不足なのか、
  それとも root layer が違っていて、
  source weighting / section ordering / article frame ownership / state flow の simpler redesign が必要なのか

deepresearch goals:
1. 日本語 blog-like article で
   - title
   - lead
   - first heading
   - first section
   が自然につながるときの role separation は何か
2. history-rich company intro で current business を first に保つための根本パターンは何か
3. variability がある生成系で、category-specific rules を積まずに安定させる minimal control layer はどこか
4. prompt accretion が効かなくなる典型パターンは何か
5. この repo の next step を
   - same owner re-implementation 継続
   - same owner simplification
   - upstream root owner reopen
   のどれにすべきか

research scope:
- Japanese writing / discourse / lead-heading-body relation
- long-form generation / document planning / coherence / content selection
- company profile / company introduction writing patterns
- production LLM system design where too many prompt constraints reduce stability
- category variance / generation variance / robustness evaluation patterns

external source preference:
- primary sources first:
  - academic papers
  - university repositories
  - reputable writing studies
  - official docs / technical blogs for LLM system design
- secondary sources only as support
- broad SEO advice / generic prompt tips / shallow blog tips は避ける

what to compare explicitly:
1. `CONTINUE_PROMPT_BUILDER_PATCHING`
   - same owner `prompt_builder.py` で company intro nonblank current-first line をさらに narrow に足す
2. `PROMPT_BUILDER_SIMPLIFICATION_FIRST`
   - generic contract と company-intro-specific line を整理し、rules を減らして frame owner を明確にする
3. `UPSTREAM_ROOT_REOPEN`
   - source weighting / compact plan / article frame ownership を upstream owner に戻して考える

evaluation criteria:
- simplicity:
  - rule を減らせるか
- robustness:
  - category variance と run variance に耐えやすいか
- explanatory compatibility:
  - V1 partial gain を壊さないか
- company intro fit:
  - history-rich source でも current-business-first を保てるか
- rollback clarity:
  - owner scope を clean に切れるか
- package alignment:
  - `prompt accretion 禁止`
  - `hidden reviser accretion 禁止`
  - `grounded generic default`
  と整合するか

strong bias:
- 「もう少し prompt line を足せば安定する」という結論を雑に出さない
- per-category hardcode accumulation を正当化しない
- skeleton / planning default reopen に戻らない
- prompt-only winner / best practice に戻らない
- current package objective を外れて giant rewrite を主張しない

what this research should read locally:
- `README.md` / `PROGRESS.md` / `ROLLBACK.md` の package constraints
- `WORKLOG.md` の historical failure memory
- `2026-04-17` deepresearch reflection docs
- `2026-04-18` live validation note / summary
- `prompt_builder.py` の company intro current-first line と generic contract line

what not to do:
- code edit
- test edit
- live rerun
- AGENTS / WORKLOG / current package docs update
- implementation plan を先に決め打ち
- 「deepresearchの結果、とにかく別モデルや別プロンプトを増やす」で逃げる

good outcome:
- current line を simpler にするか、owner を変えるかが明確になる
- next prompt type が
  - management planning
  - same-owner simplification triage
  - upstream-root triage
  のどれか1つに閉じる
- `対症療法の積み増しを止める理由` が外部 evidence と local evidence の両方で説明できる

bad outcome:
- 「とりあえずもう1本 prompt_builder の rule を増やす」で終わる
- categoryごとの tuning table を提案する
- variability を無視して single sample の感想だけで結論を出す
- research のはずが implementation に進む

recommended output file:
- `C:\tetie\notecode\docs\separate_window_heading_drift_root_simplification_deepresearch_note_2026-04-18.md`

stopping conditions:
- local package constraints と external evidence が正面衝突して結論を1本に絞れない
- research ではなく実装したくなった
- simpler root layer の候補が 3 つ以上に拡散して narrow judgment を失った

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. local failure pattern の短い要約
4. 外部 source の種類と数
5. `CONTINUE_PROMPT_BUILDER_PATCHING / PROMPT_BUILDER_SIMPLIFICATION_FIRST / UPSTREAM_ROOT_REOPEN` の比較
6. 結論
7. なぜ prompt accretion continuation ではないか
8. なぜ skeleton / planning default reopen ではないか
9. 次 prompt は management planning か、same-owner simplification triage か、upstream-root triage か
10. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
