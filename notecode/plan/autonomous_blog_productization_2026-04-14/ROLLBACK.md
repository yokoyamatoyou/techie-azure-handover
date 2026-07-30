# autonomous_blog_productization_2026-04-14 ROLLBACK

## Baseline

- restore target:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\note_writer_app.py`
- current visible artifact baseline:
  - `C:\tetie\notecode\logs\latest_generation_output.txt`
  - `C:\tetie\notecode\logs\latest_generation_output.json`
  - `C:\tetie\notecode\logs\latest_generation_quality_report.json`
- package boundary:
  - `C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\`
- keep-state boundary:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- completed reference boundary:
  - `C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\`

## Rollback Rule

- rollback は phase owner の narrow diff 単位で行う
- UI phase の rollback は visible labels / layout state / mode selector diff に閉じる
- WEB mode rollback は `source-less -> source-backed hydration` diff に閉じる
- current keep-state package docs は巻き込まない
- completed reference package は reopen しない
- telemetry だけ増えて visible safety が増えない diff は keep しない

## Do-Not-Retry Hypotheses

- source-less WEB mode を `branding/company_introduction` へ広げること
- source-less WEB mode を `announcement` へ広げること
- first screen に title / tone / CTA / SEO / persona を戻すこと
- WEB summary を source trace なしで本文生成へ渡すこと
- prompt 長文化で UI minimalism を帳消しにすること
- search / fetch / trace / evaluation を別々の新 module 群へ分割して初手から肥大化させること
- article-type fixed routing table を追加すること
- current success path を bypass する別 mainline を生やすこと

## Expected Failure Modes

- UI 簡素化のつもりで `note_writer_app.py` が巨大 diff になる
- WEB mode が source trace を保持せず raw summary に戻る
- exact date が落ちて `today / recent` の曖昧語だけが残る
- trusted source 条件が弱くて announcement 的な unsafe copy が通る
- distilled brief へ WEB context を入れすぎて prompt が再肥大化する
- final evaluation の categories が phase 中に揺れる

## Per-Phase Rollback Intention

### Phase 00 Package Lock And Baseline Freeze

- rollback:
  - package docs の新規作成分だけを戻す

### Phase 01 Minimal UI Journey

- rollback:
  - `note_writer_app.py` の first-view layout / labels / source mode selector diff だけを戻す
- current attempt note:
  - attempt 1/3 passed after shared-check unblock
  - UI diff remains the rollback unit for Phase 01

### Shared Check Unblock

- rollback:
  - `current_mainline_runner.py` の `company_introduction topic_statement execution fallback` diff だけを戻す

### Phase 02 Source Mode Contract Narrowing

- rollback:
  - `input_contract_v1.py` の source mode fields 追加分だけを戻す
- current attempt note:
  - attempt 1/3 passed
  - rollback target stays limited to `source_mode / web_research_allowed / industry_hint / source_trace_policy`

### Phase 03 WEB Research To Source Documents

- rollback:
  - `current_mainline_runner.py` の WEB query / source hydration diff と thin helper だけを戻す
- current attempt note:
  - attempt 1/3 passed
  - UI wiring rollback stays limited to `WEB mode + source無し` bypass と `source_mode` 引数伝播 diff

### Phase 04 Distilled Brief For WEB-Grounded Generation

- rollback:
  - `ui_prompt_distillation.py` の WEB digest handoff diff だけを戻す
- current attempt note:
  - attempt 1/3 passed
  - rollback target stays limited to `source_trace -> source_digest` 優先経路

### Phase 05 Guard And Trace Enforcement

- rollback:
  - `output_guard.py` の WEB mode guard / reason code diff だけを戻す
- current attempt note:
  - attempt 1/3 passed
  - rollback target stays limited to WEB blocked-category / trace-required hard fail rules

### Phase 06 Fixed Evaluation Battery And Codex Visual Review

- rollback:
  - evaluation case freeze と artifact projection diff だけを戻す
- current attempt note:
  - attempt 1/3 passed on code-side matrix freeze
  - `2026-04-14` live artifact / Codex visual review was recorded without additional code diff
  - visual review evidence stays outside rollback scope unless a future owner reopens `current_mainline_ui_matrix.py`
