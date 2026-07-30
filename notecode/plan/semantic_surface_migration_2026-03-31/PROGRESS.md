# semantic_surface_migration_2026-03-31 PROGRESS

## Current Goal

- `GPTPRO.txt` ベースの meaning-layer / surface-layer 分離を、current mainline を壊さず段階導入する

## Current Status

- Package status: completed
- Current phase: Phase 10
- Current phase status: completed
- Next action: `bl-comparative-selection-criteria` の fresh 3 reruns は `axis_shift=0,1,0` で終了し、`axis_shift=2` の same-shape recurrence は確認されなかった。this window では stochastic residual として停止し、semantic slice は開かない

## Fixed Baseline

- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> super().generate(...)`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- already introduced:
  - semantic ledger scaffold
  - semantic coverage observability
  - surface-only repair guidance
- keep state:
  - announcement kept fix
  - comparative rollback boundary
  - current UI route mapping
- rollback boundary:
  - owner-local diff only
  - primary owner max 2 files
  - support owner max 1 file
- safe activation default:
  - `explanatory_article + short|adaptive`
  - `industry_analysis + short`

## Blocked Hypotheses

- prompt accretion で押し切ること
- `human_resonance*` 本体を初手で触ること
- global parameter tuning を先行すること
- rollback 済み comparative source-grounding 仮説の再投入

## Phase Status

| Phase | Status | Notes |
|------|--------|-------|
| 00 Baseline Freeze | completed | baseline / blocked hypotheses / rollback boundary を固定 |
| 01 Semantic vs Surface Inventory | completed | omission observability を first mechanism に固定 |
| 02 Omission Observability | completed | heading reanchor miss metrics を追加 |
| 03 Omission Repair Rules | completed | omission-specific surface-only repair rule を prompt へ追加 |
| 04 Omission Activation | completed | safe scope のみ omission repair trigger を有効化 |
| 05 Ending Observability | completed | ending bucket metrics を追加 |
| 06 Ending Control | completed | bucket-aware repair controller を quality guard に固定 |
| 07 Flagged Span Patch Scaffold | completed | `PATCH_SCOPE` scaffold を repair prompt に追加 |
| 08 Flagged Span Patch Activation | completed | safe scope だけ patch path を有効化 |
| 09 Sentinel Sweep | completed | kept-state 4 genre live rerun 実施 |
| 10 Final Live And Closeout | completed | short UI matrix live / docs closeout 実施 |

## Execution Rules

- 各 phase の自己修正は 3 回まで
- 3 回失敗したら停止して user report
- 各 phase 完了後に以下を必ず確認:
  - prompt injection / policy
  - code readability
  - UI integration
  - pipeline

## Notes

- phase 開始時にこのファイルを `in_progress` へ更新する
- phase pass 後に evidence / tests / rollback note を追記する
- 停止時は `failed attempts / reason / next narrow slice` を残す

## Post-Closeout Revision

### Revised residual order

1. first slice:
   - `comparative_thin_section_targeted_patch`
   - objective:
     - `comparative_thin_section_headings` を compare-specific flagged span へ落とし、thin section だけを `PATCH_SCOPE` で局所補修する
   - owner:
     - primary: `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
     - primary: `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
   - rollback:
     - compare-specific flagged span と patch scope 文面を外せば baseline に戻る

2. second slice:
   - `comparative_compact_ledger_gate`
   - objective:
     - 新 field を増やさず、既存の compact semantic plan / `_semantic_ledger` を `comparative_review` の narrow scope にだけ有効化する
   - owner:
     - primary: `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
     - primary: `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
   - precondition:
     - fresh short compare と sentinel long compare で thin section が同じ section role に残る
     - raw axis leakage が再発していない
     - surface patch だけでは `rubric_mean_total` が頭打ち
   - rollback:
     - compare の compact-plan gate を閉じれば baseline に戻る

### Explicit do-not list

- compare 専用の新 semantic field を増やさない
- compare 専用の新 module / class を増やさない
- prompt accretion で anti-flatness を盛らない
- `human_resonance*` へ横展開しない

### 2026-04-01 compare rerun verification: `bl-comparative-selection-criteria`

- status:
  - completed
- live reruns:
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260401-selection-criteria-rerun-01`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260401-selection-criteria-rerun-02`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260401-selection-criteria-rerun-03`
- result:
  - `short_gate_passed=1/1` in all 3 reruns
  - `rubric_total=8` in all 3 reruns
  - `article_type_fit_reason=comparative_axis_locked` in all 3 reruns
  - `human_visible_ai_reason=flat_or_repetitive` in all 3 reruns
  - `comparative_axis_shift_count=0, 1, 0`
  - `prompt_echo_hits=0` in all 3 reruns
  - contract stayed aligned at `comparison_axes=価格 / 承認フロー`, `must_cover=価格 / 承認フロー / 差分`
  - when `axis_shift_count=1` appeared, it was already present at `section_generation` and remained unchanged through `after_quality` / `final_body`
- decision:
  - `axis_shift=2` same-shape recurrence was not reproduced
  - this matches the `0/3 or 1/3` branch, so treat the residual as stochastic and stop
  - do not expand to 5 reruns
  - do not open deepresearch
  - do not open `comparative_compact_ledger_gate`
  - do not change code
- keep:
  - axis normalization fix
  - tool-compare abswinner narrow fix
  - section model `gpt-5.4-mini`

## Phase Evidence

### Phase 00 Baseline Freeze

- status:
  - completed
- evidence:
  - baseline は `notecode_current_mainline_handoff_2026-03-31.md` と package docs の current success path に一致
  - blocked hypotheses は `prompt accretion` / `module accretion` / `human_resonance* first-touch` / `comparative rollback re-entry` に固定
  - rollback boundary は owner-local / narrow diff / same-phase 3 retries max に固定
- tests:
  - read-only phase のため未実行
- rollback note:
  - なし

### Phase 01 Semantic vs Surface Inventory

- status:
  - completed
- evidence:
  - `prompt_builder.py`: meaning contract / semantic ledger / generation & repair prompt owner
  - `pipeline.py`: compact semantic plan prepass / single-pass orchestration / fail-open repair owner
  - `quality_guard.py`: semantic coverage / repair trigger / rhythm observation owner
  - `rendering.py`: `pipeline_check` / telemetry projection owner
  - next mechanism は omission observability に固定。ending / flagged span patch は未着手のまま据え置き
- tests:
  - read-only phase のため未実行
- rollback note:
  - なし

### Phase 02 Omission Observability

- status:
  - completed
- evidence:
  - `quality_guard.py` に `heading_reanchor_checked_section_count` / `heading_reanchor_miss_count` / `heading_reanchor_miss_ratio` / `omission_ambiguity_score` / `omission_soft_warnings` を追加
  - 観測対象は semantic ledger がある section の見出し直後初文だけに限定し、hard fail は増やしていない
  - `rendering.py` の `pipeline_check.quality_metrics` と `contextual_naturalness_report` へ omission metrics を露出
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
- rollback note:
  - metrics 追加だけを戻せば baseline へ復帰可能

### Phase 03 Omission Repair Rules

- status:
  - completed
- evidence:
  - `prompt_builder.py` の repair prompt へ omission-specific rule builder を追加
  - omission rule は `diagnostics.omission_repair_active=true` のときだけ有効で、claim / anchor 維持と冒頭2文だけの局所補修に固定
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
- rollback note:
  - omission rule builder を外せば baseline へ戻る

### Phase 04 Omission Activation

- status:
  - completed
- evidence:
  - `pipeline.py` で omission activation boundary を `_compact_plan_safe_scope()` に固定
  - safe scope は `explanatory_article + short|adaptive` と `industry_analysis + short` のみ
  - out-of-scope route では omission metrics を残したまま repair trigger へ昇格させていない
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
- rollback note:
  - `_activate_omission_repair()` を戻せば safe-scope activation を即解除できる

### Phase 05 Ending Observability

- status:
  - completed
- evidence:
  - `quality_guard.py` に `ending_bucket_counts` / `ending_bucket_max_run` / `ending_bucket_monotony_score` を追加
  - bucket は `polite` / `plain_assertive` / `soft_modal` / `reason_explanatory` / `other` に固定
  - `rendering.py` の `quality_metrics` と `contextual_naturalness_report` へ ending bucket metrics を露出
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
- rollback note:
  - ending bucket metrics 追加だけを戻せば baseline へ復帰可能

### Phase 06 Ending Control

- status:
  - completed
- evidence:
  - generic な `文末を散らす` 指示をやめ、bucket-aware repair control へ置換
  - `quality_guard.py` は `ending_bucket_max_run >= 3` のときだけ fixed controller 文面を追加
  - `soft_warnings` に `ending:bucket_monotony` を追加し、観測と control の境界を固定
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
- rollback note:
  - bucket control line builder を外せば旧 generic instruction に戻せる

### Phase 07 Flagged Span Patch Scaffold

- status:
  - completed
- evidence:
  - `prompt_builder.py` の repair prompt に `PATCH_SCOPE` block を追加
  - scaffold は `issue_type / section_heading / sentence_window` の fixed schema に限定
  - full draft input は維持しつつ、変更範囲だけを deterministic に縛る形で narrow 導入した
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
- rollback note:
  - `PATCH_SCOPE` block と flagged span summary を外せば baseline へ戻る

### Phase 08 Flagged Span Patch Activation

- status:
  - completed
- evidence:
  - `pipeline.py` に flagged span builder と patch activation 判定を追加
  - activation scope は safe scope のみ、issue type は `heading_reanchor` / `ending_bucket_monotony` の 2 つだけ
  - repair metadata に `patch_path_available` / `patch_path_used` / `flagged_span_count` を残す
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
- rollback note:
  - patch activation helper を戻せば scaffold は残したまま activation だけ切れる

### Phase 09 Sentinel Sweep

- status:
  - completed
- evidence:
  - live rerun artifact:
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260331-202056-genre-rerun\summary.json`
  - kept-state 4 genre rerun:
    - `branding 5/5, rubric_mean_total=7.4`
    - `announcement 4/5, rubric_mean_total=6.0`
    - `case_study 5/5, rubric_mean_total=6.4`
    - `comparative_review 5/5, rubric_mean_total=7.0`
  - short gate は `19/20`
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\tools\run_current_mainline_genre_sweep.py --phase genre-rerun --live --genres branding,announcement,case_study,comparative_review`
- rollback note:
  - code rollback は不要。sentinel artifact だけ保持

### Phase 10 Final Live And Closeout

- status:
  - completed
- evidence:
  - live short UI matrix:
    - `C:\tetie\notecode\logs\current_mainline_ui_short_matrix_latest.json`
    - artifact dir: `C:\tetie\notecode\logs\current_mainline_ui_runs\20260331-202450-short\`
  - result:
    - `short_gate_passed=10/10`
    - `battery_rubric_mean_total=7.9`
    - `runtime_models=gpt-5.4-mini`
    - blocker:
      - `rubric_mean_total=7.9<8.0`
  - safe-scope live cases:
    - `ui-short-explanatory-default: 8/10`
    - `ui-short-industry-analysis: 8/10`
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\tools\run_current_mainline_ui_matrix.py --phase short --live`
- rollback note:
  - kept residual は `comparative_review` rubric uplift と fixed genre stochastic watch。semantic/surface package 自体は keep

### Post-Closeout Execution: comparative_thin_section_targeted_patch

- status:
  - completed
- code:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
    - `comparative_thin_section_headings` を compare-specific flagged span (`issue_type=comparative_thin_section`) へ接続
    - `comparative_review` だけ safe-scope 例外で patch path を有効化
    - `repair_call.flagged_issue_types` / `repair_call.compare_thin_section_headings` を evidence 用に追加
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
    - `PATCH_SCOPE` に compare thin section 専用の narrow repair 文面を追加
    - span 指定見出しだけを 2-3 文へ補修し、winner claim / candidate / axis の追加を禁止
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `37 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `9 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `77 passed`
- live:
  - `C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\tools\run_current_mainline_genre_sweep.py --phase genre-rerun --live --genres comparative_review`
  - artifact dir:
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260331-221210-genre-rerun`
  - result:
    - `short_gate_passed=5/5`
    - `rubric_mean_total=7.0`
    - compare `.txt` artifact では raw axis token (`review_flow` / `onboarding` / `support_density` / `approval_flow` / `governance`) の新規再発なし
- evidence:
  - owner-local test `test_simple_note_pipeline_uses_compare_thin_section_patch_path` で `patch_path_used=true` と `compare_thin_section_headings` を固定
  - live rerun 自体は compare thin section residual を再現せず、artifact 上の `patch_path_used` は未発火のまま
  - したがって keep evidence は `required checks + live no-regression + owner-local patch-path proof` の組み合わせで残す
- rollback note:
  - keep。`comparative_compact_ledger_gate` には進まない

### 2026-04-01 update: cross-department discourse planner narrow slice

- status:
  - attempted, rolled back
- scope:
  - `st-comparative-cross-department` only
  - semantic gate closed
  - `section=gpt-5.4-mini` fixed
  - `section_generator.py` failed slimming was not reused
- owner tried:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py`
- hypothesis:
  - no-source cross-department compare の `fit / caution / closing` seed を axis-specific に狭める
- owner-local:
  - implementation 時点では pass
  - rollback 後 baseline confirm:
    - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st05ab8 or st05ab9 or st05ab10" -q`
    - `3 passed`
- live targeted rerun:
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260401-cross-department-discourse-rerun-01`
    - `short_gate=1/1`, `rubric=8`, `prompt_echo=0`, `axis_shift=0`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260401-cross-department-discourse-rerun-02`
    - `short_gate=0/1`, `rubric=6`, `prompt_echo=1`, `axis_shift=1`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260401-cross-department-discourse-rerun-03`
    - `short_gate=1/1`, `rubric=8`, `prompt_echo=0`, `axis_shift=0`
- visible residual:
  - rerun-02 prompt echo:
    - `複数部門で記事作成を回すなら、承認フローだけを短くしても、責任の置き方が曖昧だと運用は安定しにくいです。`
- decision:
  - not kept
  - owner-local diff rolled back
  - full compare 5-case rerun skipped
- next narrow slice:
  - TBD
  - do not re-submit the same `discourse_planner.py` hypothesis unchanged
