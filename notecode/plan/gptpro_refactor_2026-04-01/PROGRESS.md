# gptpro_refactor_2026-04-01 PROGRESS

## Current Goal

- `GPTPRO.txt` ベースの rollback 可能な新 refactor package を current execution package として開始し、current success path を維持したまま narrow phase で進める

## Current Status

- Package status: completed
- Current phase: Phase 08 Final Live And Visual Loop
- Status: completed
- Hypothesis:
  - fixed 3 cases を 1 loop で安定させる
- Owner scope:
  - live loop
- Attempts used: 1/3
- Next phase:
  - complete

## Fixed Baseline

- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- keep state:
  - compare axis normalization fix
  - compare opener / ranking soften
  - tool-compare abswinner narrow fix
  - compare repeated ending diversification の安全版
- completed baseline package:
  - `C:\tetie\notecode\plan\semantic_surface_migration_2026-03-31\`

## Blocked Hypotheses

- prompt accretion で押し切ること
- `human_resonance*` を初手で触ること
- rollback 済み compare source-grounding 仮説の再投入
- `section_generator.py` の failed slimming 再投入
- 2026-04-01 `discourse_planner.py` cross-department hypothesis の unchanged 再投入
- prompt echo detector threshold 調整や output formatter 止血で逃げること

## Phase Ledger

| Phase | Status | Hypothesis | Owner scope | Attempts | Evidence | Next phase |
|------|--------|------------|-------------|----------|----------|------------|
| 00 Baseline Freeze | completed | baseline / rollback / blocked hypotheses を package に固定する | package docs only | 0/3 | `README.md` / `TASK.md` / `ROLLBACK.md` に baseline と boundary を固定 | 01 |
| 01 Responsibility Inventory | completed | next mechanism を 1 owner scope に絞る | package docs only | 0/3 | `input_contract.py=contract` / `prompt_builder.py=shadow prompt & repair` / `simple_note_pipeline/pipeline.py=realization` / `quality_guard.py=guard` / `rendering.py=telemetry` / `quality_observability_mixin.py=compare observability` / `output_formatter.py=surface safe fix` を棚卸し | 02 |
| 02 Contract Narrow Hardening | completed | existing contract だけで later shadow spec 用の bounded internal summary を作る | `input_contract.py` + owner-local tests | 1/3 | `_shadow_spec_inputs` を internal bundle として導入。tests: `24/39/9/77 passed` | 03 |
| 03 Section Shadow Spec | completed | section shadow representation を prompt builder owner に閉じる | `prompt_builder.py` + owner-local tests | 1/3 | `SECTION_SHADOW` block を compact plan がある場合だけ generation prompt へ導入。tests: `24/39/9/77 passed` | 04 |
| 04 Controlled Realization | completed | shadow -> prose drift を pipeline owner で fail-open 制御する | `simple_note_pipeline/pipeline.py` + owner-local tests | 1/3 | controlled realization guard と `shadow_section_drift` span を追加。tests: `24/41/9/77 passed` | 05 |
| 05 Local Patch Alignment | completed | flagged span patch を shadow-aligned local repair に寄せる | `prompt_builder.py` + owner-local tests | 1/3 | `SECTION_SHADOW` を repair prompt に通し、`shadow_patch` scope lines を追加。tests: `24/42/9/77 passed` | 06 |
| 06 Comparative Stabilization | completed | `st-comparative-cross-department` を新構造で narrow に安定化する | `newalgorithm_pipeline/pipeline.py` + owner-local tests | 2/3 | cross-department comparative final-body stabilizer を追加。owner-local subset pass、live rerun-03/04/05 で `prompt_echo_hits=0` / `axis_shift=0` / short_gate 3/3 pass | 07 |
| 07 Sentinel Sweep | stopped | announcement residual は pipeline owner で narrow fix できるが、rerun 後に branding title echo が残り、次は `output_formatter.py` owner へ移る | `newalgorithm_pipeline/pipeline.py` + live checks | 1/3 | initial sentinel で `bl-announcement-spec-change` fail。announcement fix 後の rerun で announcement 5/5 pass、ただし `bl-branding-values-stance` が title prompt echo で fail。次 diff は `output_formatter.py` owner となり `1 phase = 1 owner scope` を超えるため停止 | user report |
| 07a Branding Title Prompt Echo Fix | completed | `_prefer_generated_title` に topic-overlap + mid-title sentence boundary ガードを追加して prompt echo title を reject する | `output_formatter.py` + owner-local tests | 1/3 | sentinel 20/20 pass。branding 5/5。`bl-branding-values-stance` prompt_echo_hits=0 | 08 |
| 08 Final Live And Visual Loop | completed | fixed 3 cases を 1 loop で安定させる | live loop | 1/3 | Loop 1 で 3/3 pass。目視確認 OK | complete |

## Progress Discipline

- phase 開始時に current phase / status / hypothesis / owner scope / attempts を更新する
- phase pass 後に evidence / tests / rollback note / next phase を更新する
- 停止時は `failed attempts / failed hypothesis / visible residual / next narrow slice` を必ず残す

## Phase Evidence

### Phase 00 Baseline Freeze

- status:
  - completed
- evidence:
  - new package の read order / source-of-truth priority / current success path / keep state / non-goals を固定
  - `ROLLBACK.md` に baseline / restore targets / per-phase rollback boundary / do-not-retry hypotheses を固定
- tests:
  - docs only
- rollback note:
  - なし

### Phase 01 Responsibility Inventory

- status:
  - completed
- evidence:
  - `input_contract.py`: contract resolve と bounded internal summary owner
  - `prompt_builder.py`: generation / repair prompt owner
  - `simple_note_pipeline/pipeline.py`: realization / fail-open orchestration owner
  - `quality_guard.py`: repair trigger / observability owner
  - `rendering.py`: telemetry projection owner
  - `quality_observability_mixin.py`: compare observability owner
  - `output_formatter.py`: kept surface-safe post-format owner
- tests:
  - docs only
- rollback note:
  - なし

### Phase 02 Contract Narrow Hardening

- status:
  - completed
- hypothesis:
  - existing contract fields だけで later shadow spec 用の bounded internal summary を導出する
- owner scope:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
  - `C:\tetie\notecode\note\tests\test_newalgorithm_phase01_contract.py`
- evidence:
  - `input_contract.py` に `_shadow_spec_inputs` を追加
  - payload は `main_focus / support_points / goal_bias / must_cover / comparison_axes / source_fact_pool / allowed_pronouns / relationship_mode / register_policy` を bounded に保持
  - new public field は増やしていない
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase01_contract.py -q`
    - `24 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `39 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `9 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `77 passed`
- rollback note:
  - `_shadow_spec_inputs` を戻せば baseline へ復帰可能

### Phase 03 Section Shadow Spec

- status:
  - completed
- hypothesis:
  - compact plan と `_shadow_spec_inputs` を合成した `SECTION_SHADOW` block を prompt builder owner だけで導入する
- owner scope:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- evidence:
  - compact plan がある場合だけ `SECTION_SHADOW` block を generation prompt に追加
  - block は `shadow[n]=heading / focus / claim / support / axes / fact / voice` で bounded に保持
  - compact plan がないケースは fail-open で block を出さない
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase01_contract.py -q`
    - `24 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `39 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `9 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `77 passed`
- rollback note:
  - `SECTION_SHADOW` block と summary helper を戻せば baseline へ復帰可能

### Phase 04 Controlled Realization

- status:
  - completed
- hypothesis:
  - `SECTION_SHADOW` と `_shadow_spec_inputs` がある場合だけ controlled realization を有効化し、shadow drift を fail-open のまま局所 repair へ送る
- owner scope:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- evidence:
  - `pipeline.py` に controlled realization guard を追加
  - `shadow_section_drift` を pipeline owner 内で検知し、`flagged_spans` と repair metadata に反映
  - `pipeline_check.body_generation.controlled_realization` に initial/final drift telemetry を追加
  - shadow input がないケースは fail-open のまま inactive を維持
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase01_contract.py -q`
    - `24 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `41 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `9 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `77 passed`
- rollback note:
  - `pipeline.py` の controlled realization helper / `shadow_section_drift` span / telemetry injection を戻せば baseline へ復帰可能

### Phase 05 Local Patch Alignment

- status:
  - completed
- hypothesis:
  - `shadow_section_drift` を prompt builder owner だけで focus / claim / support を保つ local patch prompt に落とせる
- owner scope:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- evidence:
  - repair prompt に target heading 限定の `SECTION_SHADOW` block を追加
  - `shadow_patch=...` scope lines を追加し、未指定 heading の rewrite を抑制
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase01_contract.py -q`
    - `24 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `42 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `9 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `77 passed`
- rollback note:
  - `prompt_builder.py` の shadow patch scope lines と repair-side `SECTION_SHADOW` block を戻せば baseline へ復帰可能

### Phase 06 Comparative Stabilization

- status:
  - completed
- hypothesis:
  - cross-department compare の closing prompt-echo を `newalgorithm_pipeline/pipeline.py` の final-body stabilizer だけで止められる
- owner scope:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - comparative owner-local subset tests
- evidence:
  - `pipeline.py` に cross-department comparative closing stabilizer を追加
  - cross-department compare だけ、closing の prompt-echo を axis-grounded sentence へ置換
  - comparative final body 後に editor guard を再適用し、quality stage 由来の fragment を拾う
  - live artifact:
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260402-gptpro-phase06-rerun-03`
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260402-gptpro-phase06-rerun-04`
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260402-gptpro-phase06-rerun-05`
  - live result:
    - short_gate `3/3`
    - rubric `8/8/8`
    - `prompt_echo_hits=0`
    - `comparative_axis_shift_count=0`
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st07g0 or st07g0a or st07h or st07e or st07g" -q`
    - `21 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase01_contract.py -q`
    - `24 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `42 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `9 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `77 passed`
- rollback note:
  - `pipeline.py` の cross-department closing stabilizer / comparative final-body editor-guard reapply / stage-diagnostic report split を戻せば baseline へ復帰可能

### Phase 07 Sentinel Sweep

- status:
  - stopped
- hypothesis:
  - initial sentinel fail の announcement prompt echo だけを `newalgorithm_pipeline/pipeline.py` owner で narrow fix すれば 4 genre rerun を通せる
- owner scope:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - live checks
- evidence:
  - initial artifact:
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260402-gptpro-phase07-sentinel`
    - `bl-announcement-spec-change` が `prompt_echo_hits=1`
  - code diff:
    - `announcement` の target section だけ、prompt echo sentence を role-aligned sentence に置換する final-body stabilizer を追加
  - rerun artifact:
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260402-gptpro-phase07-sentinel-rerun-01`
  - rerun result:
    - `announcement: pass=5/5`
    - `comparative_review: pass=5/5`
    - `case_study: pass=5/5`
    - `branding: pass=4/5`
    - residual fail:
      - `bl-branding-values-stance`
      - title prompt echo:
        - `機能の多さより、現場で迷わない設計を重視する会社の姿勢紹介記事。`
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st07g6aa or st07g6a or st07g0 or st07g0a or st07h or st07e or st07g" -q`
    - `22 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase01_contract.py -q`
    - `24 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `42 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `9 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `77 passed`
- rollback note:
  - announcement stabilizer 自体は rollback 可能だが、Phase 07 の next fix は `output_formatter.py` owner へ移り、`1 phase = 1 owner scope` を満たせないためここで停止する

### Phase 07a Branding Title Prompt Echo Fix

- status:
  - completed
- hypothesis:
  - `_prefer_generated_title` に topic-overlap + mid-title sentence boundary ガードを追加すれば、LLM 生成 title の prompt echo を reject し `_compact_title` fallback で適切な title を出せる
- owner scope:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
  - `C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py`
- evidence:
  - `output_formatter.py` に `_is_title_prompt_echo(title, topic)` helper を追加
  - topic-overlap（common prefix >= 20）と mid-title sentence boundary（`。！？` が title 内部に出現）の 2 条件で prompt echo title を reject
  - `_prefer_generated_title` に `topic` kwarg を追加し、`format_output` から渡す
  - `bl-branding-values-stance` の title が `"現場で迷わない導入を支える、テティエ株式会社の考え方"` に改善、`prompt_echo_hits=0`
  - sentinel artifact:
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260402-gptpro-phase07a-sentinel`
  - sentinel result:
    - `short_gate_passed=20/20`
    - `rubric_mean_total=7.25`
    - `announcement: pass=5/5`
    - `branding: pass=5/5`
    - `case_study: pass=5/5`
    - `comparative_review: pass=5/5`
    - 全 4 genre で `prompt_echo_case_ids=[]`
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st07a" -q`
    - `9 passed`（Phase 07a 新規 7 + 既存 st07aa/st07ab 2）
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase01_contract.py -q`
    - `24 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `42 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `9 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `77 passed`
- rollback note:
  - `output_formatter.py` の `_is_title_prompt_echo` helper と `_prefer_generated_title` の `topic` kwarg ガードを戻せば baseline へ復帰可能

### Phase 08 Final Live And Visual Loop

- status:
  - completed
- evidence:
  - Loop 1 で 3/3 pass。目視確認 OK。2 loop 目は不要
  - `st-comparative-cross-department`:
    - artifact: `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260402-gptpro-phase08-loop01`
    - `short_gate=pass`, `rubric=8`, `prompt_echo_hits=0`
    - title: `承認フローと担当責任の置き方で見る選定基準`
  - `ui-short-announcement-dense-must-cover`:
    - artifact: `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260402-gptpro-phase08-loop01-short`
    - `short_gate=pass`, `prompt_echo_hits=0`
    - title: `2026年5月15日のSSO設定変更について`
  - `ui-short-case-study-explain`:
    - artifact: `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260402-gptpro-phase08-loop01-short`
    - `short_gate=pass`, `prompt_echo_hits=0`
    - title: `初回設定で迷いやすい案内導線を、担当者別に整理し直した話`
- visual review:
  - 3 本とも title / lead / body に prompt echo や meta text 混入なし
  - comparative は 5 section に沿って比較軸が整理されている
  - announcement は変更内容→対象→事前準備の順で過不足なし
  - case_study は迷いの起点→組み替え→結果→再現条件の流れ。最終 section にやや反復あるが hard fail ではない
- rollback note:
  - なし（code edit なし）

---

## 2026-04-02 追記（company introduction voice retune）

### 実施範囲
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\simple_note_pipeline\rendering.py`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- `C:\tetie\notecode\note\simple_note_pipeline\style_learner.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- `C:\tetie\notecode\note\tests\test_simple_note_quality_guard.py`

### attempt1
- hypothesis:
  - company introduction の voice を `HARD_CONTRACT` へ強めに入れれば、誰視点を前に出したまま会社紹介らしい本文になる
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - initial patch で `1 failed`
- live artifact:
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-branding-perspective-20260402-attempt1`
- live result:
  - `short_gate=pass`
  - `rubric=6`
  - `source_grounding_reflection_ratio=0.6667`
- rollback note:
  - failed hypothesis と判断し、company voice の hard-contract injection は rollback 済み

### attempt2
- hypothesis:
  - company voice は `STRUCTURE` guidance に留め、`社名や『当社』を機械的に繰り返さない` を明示すれば、視点を強めつつ flatness を悪化させない
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `43 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `10 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase01_contract.py -q`
    - `24 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `77 passed`
- live artifact:
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-branding-perspective-20260402-attempt2`
- live result:
  - `short_gate=pass`
  - `rubric=8`
  - `source_grounding_reflection_ratio=1.0`
- keep:
  - attempt2 を keep する

---

## 2026-04-02 追記（section rhythm retune for flat section / linebreak feel）

### 実施範囲
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

### 目的
- company introduction / explanatory / announcement で見えていた
  - section ごとの文字量が近すぎる
  - 改行の入り方が均一すぎる
  - 一文だけの独立段落が連続して AI っぽく見える
  を prompt 側の narrow diff で緩和する

### keep state
- keep diff:
  - `STRUCTURE` に
    - `全見出しを同じ厚みで並べず、短めの節・中くらいの節・厚めの節を混ぜる。全節を1段落固定にしない。`
  - company introduction 向けに
    - `導入や締めはやや短め、判断材料や支え方を説明する節はやや厚めでもよい。全節を同じ分量・同じ改行数でそろえない。`
  - `HARD_CONTRACT` に
    - `一文だけの独立段落を連続させない。`

### 5-run live evidence
- cases:
  - `bl-branding-values-stance`
  - `bl-explanatory-misread-metric`
  - `bl-announcement-spec-change`
- run1:
  - artifact:
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-section-rhythm-20260402-r1`
  - result:
    - `rubric_mean_total=6.67`
    - `branding=7 / explanatory=7 / announcement=6`
  - verdict:
    - rollback
    - `span=lean|standard|thick` + `SECTION_RHYTHM` block は過制約
- run2:
  - artifact:
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-section-rhythm-20260402-r2`
  - result:
    - `rubric_mean_total=7.67`
    - `branding=8 / explanatory=7 / announcement=8`
  - verdict:
    - provisional keep
- run3:
  - artifact:
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-section-rhythm-20260402-r3`
  - result:
    - `rubric_mean_total=8.0`
    - `branding=8 / explanatory=8 / announcement=8`
  - verdict:
    - best keep
    - 3 case すべてで short_gate pass、視認でも section の均一感が最も薄い
- run4:
  - artifact:
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-section-rhythm-20260402-r4`
  - result:
    - `rubric_mean_total=7.0`
    - `branding=6 / explanatory=8 / announcement=7`
  - verdict:
    - rollback
    - anti-fragment paragraph bundling line が branding / announcement を悪化
- run5:
  - artifact:
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-section-rhythm-20260402-r5`
  - result:
    - `rubric_mean_total=7.67`
    - `branding=8 / explanatory=7 / announcement=8`
  - verdict:
    - rollback 後の candidate は再現可能だが、best は run3

### tests
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
  - `43 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase01_contract.py -q`
  - `24 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
  - `10 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
  - `77 passed`

### verdict
- section rhythm 対策は prompt 側の軽い guidance までなら keep できる
- 配分 schema や paragraph bundling の hard guidance は do-not-retry

## 2026-04-02 追記（product introduction short-body stabilization）

### owner scope
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- `C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

### hypothesis
- 最新通常ログ `gen-15e85475` の短文化は prompt 全体ではなく `branding / product_introduction` の thin-body path に局所化している
- `simple_note_pipeline` 側の repair ではなく、current runtime の `newalgorithm_pipeline` 最終段で薄い本文だけを補う narrow diff なら、肥大化を避けながら `body_chars` と `must_cover` 反映を戻せる

### keep diff
- `branding / product_introduction` 専用の `_stabilize_thin_product_intro_body()` を追加
- 発火条件は
  - `body_chars < 780`
  - かつ短文化パターン
    - `body_chars < 520` の場合は one-sentence section `>= 2`
    - `body_chars >= 520` の場合は one-sentence section `>= 3`
- 追加文は各節 1 文までに限定し、`core_message` / `must_cover` / `source_grounding_items` を局所補強する
- `_stabilize_thin_source_grounded_body()` に `contract` を渡すよう変更
- 前回効かなかった `simple_note_pipeline` 側の product-intro repair test は rollback

### evidence
- baseline:
  - `C:\tetie\notecode\logs\latest_generation_output.json`
  - `body_chars=420`
  - `must_cover_reflection_ratio=0.0`
  - `source_grounding_reflection_ratio=0.8333`
- local replay:
  - 同本文に stabilizer を適用すると `420 -> 702`
- live 3-run artifact:
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-thin-product-intro-live-3run-20260402-164128`
- live 3-run summary:
  - run01: `body_chars=702`, `single_sentence_paragraph_ratio=0.0`, `must_cover_reflection_ratio=1.0`, `source_grounding_reflection_ratio=1.0`
  - run02: `body_chars=702`, `single_sentence_paragraph_ratio=0.0`, `must_cover_reflection_ratio=1.0`, `source_grounding_reflection_ratio=1.0`
  - run03: `body_chars=702`, `single_sentence_paragraph_ratio=0.0`, `must_cover_reflection_ratio=1.0`, `source_grounding_reflection_ratio=1.0`
- visual verdict:
  - 「短すぎて薄い」は解消
  - 追加文はまだ少し補助文として見えるが、前回の 420-char body より明確に改善
  - keep

### tests
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st07g6a or st07g6ab or st07g6ac" -q`
  - `6 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py note\tests\test_newalgorithm_phase01_contract.py note\tests\test_simple_note_pipeline.py -q`
  - `144 passed`

### next
- 追加文の「補助線っぽさ」をさらに薄くしたい場合は、section 1 / 4 の補強文だけを owner-local に言い換える
- ただし現時点では short-body failure の再現が止まっているため、まずは keep state を優先する

## 2026-04-02 追記（web research 後の section-shape controller 試行は rollback）

### external research
- 長文生成の安定化は prompt accretion より
  - content planning
  - outline/controller
  - intermediate blueprint
  を分ける方が安定、という一次情報を確認
- 参考:
  - DOC: a detailed-outliner and controller for long text generation
  - Plan-and-Write
  - TextBlueprint

### hypothesis
- current mainline でも `discourse_planner -> section_generator` の contract に既に `target_chars` / `paragraph_min/max` がある
- なので prompt を増やすより、section shape contract を controller で守らせるほうが本筋

### attempt
- `section_generator.py`
  - paragraph contract mismatch 時の local shape retry controller を追加
- `pipeline.py`
  - `branding / product_introduction` の compatibility body に mixed paragraph shape を追加

### live result
- artifact:
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-shape-controller-compat-live-3run-20260402-172108`
- result:
  - `body_chars=708`
  - `paragraph_count=13`
  - `single_sentence_paragraph_ratio=0.375`
  - `must_cover_reflection_ratio=1.0`
  - `source_grounding_reflection_ratio=1.0`
- visual verdict:
  - section 内改行は増えた
  - ただし `価値` / `現場` / `次の一歩` で一文独立段落が増え、自然な段落差ではなく「段落を足した感」が強い
  - keep 不可

### rollback
- 上記 2 変更は rollback 済み
- kept state は引き続き
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-thin-product-intro-live-3run-20260402-164128`
  - `body_chars=702`
  - `single_sentence_paragraph_ratio=0.0`

### takeaway
- section shape を planner/controller 側で扱う方向自体は妥当
- ただし compatibility body に blank-line をそのまま差し込む実装は粗く、one-sentence paragraph excess を起こす
- 次にやるなら
  - compatibility body の whole-body replace をやめる
  - section 単位で native body と fallback body を選ぶ merge controller
  の方が筋

## 2026-04-05 追記（current mainline genre validation after completed package）

### scope
- current success path は維持:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- validation matrix:
  - `explanatory_article`: `bl-explanatory-misread-metric`
  - `announcement`: `bl-announcement-spec-change`
  - `branding/product_introduction`: `bl-branding-service-overview`
  - `branding/company_introduction`: `bl-branding-company-overview`
  - `industry_analysis`: `bl-industry-evaluation-shift`
  - `case_study`: `bl-case-improvement`
  - `comparative_review`: `bl-comparative-selection-criteria`

### baseline
- artifact:
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260405-baseline1`
- result:
  - `short_gate_passed=7/7`
  - `rubric_mean_total=7.14`
- dominant failure:
  - `branding/product_introduction`
  - route-local drift。`brand writer role -> knowledge_lens -> must_cover/support_points` と thin-body stabilizer の組み合わせで、source 非整合の generic 補助文が混入

### narrow fix 1
- owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
- hypothesis:
  - `product_introduction` では writer-role 由来の branding lens を content contract に昇格させない
- backup:
  - `C:\tetie\notecode\backups\2026-04-05_product_route_fix1_pre`
- keep diff:
  - `product_introduction` の `support_points` / `must_cover` から `企業ブランディングの観点で価値の伝え方を整える` を除外
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase01_contract.py -q`
    - `29 passed`
  - shared checks
    - `65/14/83 passed`
- live rerun artifacts:
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260405-fix1-rerun1`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260405-fix1-rerun2`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260405-fix1-rerun3`
- verdict:
  - `branding/product_introduction` の `must_cover_reflection_rate` は `1.0` まで改善
  - ただし本文 drift 自体は残存し、次 blocker は `pipeline.py` owner の thin-body stabilizer

### narrow fix 2
- owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- hypothesis:
  - `branding/product_introduction` thin-body stabilizer の generic 補助文を route-specific 文へ置換すれば、source と route に沿った本文へ戻せる
- backup:
  - `C:\tetie\notecode\backups\2026-04-05_product_route_fix2_pre`
- keep diff:
  - `紙資料/帳票/入力納品` 系の補助文を削除
  - `設定順 / 案内分岐 / FAQ / 管理者負荷` ベースの補助文へ差し替え
- owner-local tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st07g6ab or st07g6ac or st07g6ad or st07g6ae" -q`
    - `5 passed`
- shared checks:
  - `65/14/83 passed`
- live rerun artifacts:
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260405-fix2-rerun1`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260405-fix2-rerun2`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260405-fix2-rerun3`

### final reading
- stable:
  - `branding/product_introduction`: `3/3 pass`, `rubric mean 8.0`
  - `comparative_review`: `3/3 pass`, `rubric mean 8.0`
  - `explanatory_article`: `3/3 pass`, `rubric mean 7.67`
- conditionally stable:
  - `announcement`: `3/3 pass`, `rubric mean 7.0`
  - `branding/company_introduction`: `3/3 pass`, `rubric mean 7.33`
- unresolved:
  - `case_study`: `3/3 short_gate pass` だが `rubric mean 6.33`。result / condition 節が薄く、ブログとしての伸びが足りない
  - `industry_analysis`: `2/3 pass`。`fix2-rerun2` で本文 prompt echo 1 hit

### next narrow slices
- `case_study`
  - owner 候補: `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - result / condition section の source-grounded backfill を局所化
- `industry_analysis`
  - owner 候補: `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py` または `prompt echo` 局所 guard
  - title/body の mid-sentence prompt echo を route-local に止める

## 2026-04-05 追記（case_study source assignment root-cause cut）

### hypothesis
- `case_study / implementation_case` の弱さは source 不足ではなく `discourse_planner` の source assignment
- sparse source が前半節で消費され、`change / condition` に evidence が届かないため、後段で abstract 化や raw default 置換が起きやすい

### owner
- `C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py`

### backup
- `C:\tetie\notecode\backups\2026-04-05_case_study_route_fix1_pre`

### keep diff
- `case_study` 用に source fact の lightweight route bucket を `discourse_planner` 内だけで推定
  - `before / process / change / condition`
- sparse source の優先割当を `hook/problem -> change -> condition -> practice` 側へ寄せた
- item 数が少ない場合でも `change / condition` 節に最低 1 本 evidence を渡す route-local reserve を追加
- 後段 stabilizer / formatter / prompt accretion は未変更

### owner-local tests
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st05ab7c or st05ab7d or st07g6 or case_study_discourse_plan_reserves_change_and_condition_sections" -q`
  - `12 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_natural_blog_core.py -k "case_study_discourse_plan" -q`
  - `2 passed`

### shared checks
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
  - `65 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
  - `14 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
  - `83 passed`

### live rerun artifacts
- `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260405-casefix1-rerun1`
- `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260405-casefix1-rerun2`
- `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260405-casefix1-rerun3`

### live reading
- aggregate:
  - `explanatory_article`: `3/3 pass`, `rubric mean 8.0`
  - `announcement`: `3/3 pass`, `rubric mean 7.33`
  - `branding`: `6/6 pass`, `rubric mean 7.67`
  - `industry_analysis`: `2/3 pass`, `rubric mean 7.33`
  - `comparative_review`: `3/3 pass`, `rubric mean 7.33`
  - `case_study`: `3/3 pass`, `rubric mean 6.67`
- `case_study` では `change / condition` の `source_grounding_items` が live artifact 上で埋まり、`source_trace_coverage` は `0.6667 -> 1.0` を含む形まで回復
- ただし acceptance ではない
  - `結果として何が変わったか`
  - `どの条件なら再現できるか`
  の prose が source 文の直置き寄りで、ブログ本文としてはまだ硬い

### verdict
- keep 可
  - source evidence starvation という root cause は切れた
- ただし unresolved
  - 残件は source assignment ではなく、assigned fact を section intent に沿った自然文へ変換する layer
  - 次 phase は `section generation` 側を owner にして、`case_study change/condition` の section intent と source rendering を narrow に見る

## 2026-04-05 追記（case_study section-generator localization rollback）

### hypothesis
- `case_study` 後半 2 節の読みにくさは、`section_generator` に入る `user_instruction / anchor_terms` が見出し語レベルで弱いことが主因
- `change / condition` の generation contract を局所強化すれば、result / condition が source 文直置きから自然 prose 側へ寄る

### owner
- `C:\tetie\notecode\note\newalgorithm_pipeline\section_generator.py`

### backup
- `C:\tetie\notecode\backups\2026-04-05_case_study_route_fix2_pre`

### attempted diff
- `case_study change`
  - `section_user_instruction` を「何がどう変わったかを先に置き、その変化がなぜ効いたかまで書く」へ局所上書き
  - anchor を `状態変化 / 読者に見える変化 / なぜ効いたか` へ寄せた
- `case_study condition`
  - `section_user_instruction` を「向く条件、前提、限界を分け、進め方の再説明ではなく適用条件として書く」へ局所上書き
  - anchor を `向く条件 / 前提 / 限界 / 効きにくい場面` へ寄せた
- owner-local guard に
  - result 節で進め方再説明に戻らない
  - condition 節で向く条件・前提・限界を分ける
  を追加

### owner-local tests
- keep 前の検証
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st05ab3 or st05ab7 or st07g6aa_case_study_change_fallback_fact_strips_condition_clause or st07i_non_comparative_stage_diagnostic_is_disabled" -q`
    - `13 passed`
- rollback 後の再確認
  - 同コマンド
    - `11 passed`

### shared checks
- rollback 後
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `65 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `14 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `83 passed`

### live rerun artifacts
- `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260405-casefix2-rerun1`
- `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260405-casefix2-rerun2`
- `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260405-casefix2-rerun3`

### live reading
- aggregate
  - `explanatory_article`: `3/3 pass`, `rubric mean 7.67`
  - `announcement`: `3/3 pass`, `rubric mean 7.33`
  - `branding`: `6/6 pass`, `rubric mean 8.0`
  - `industry_analysis`: `3/3 pass`, `rubric mean 8.0`
  - `comparative_review`: `3/3 pass`, `rubric mean 8.0`
  - `case_study`: `3/3 pass`, `rubric mean 5.67`
- `case_study` は `condition sentence count` 自体は通るが、acceptance は悪化
  - `rerun1`: `score 6`
  - `rerun2`: `score 5`
  - `rerun3`: `score 6`
- 目視でも
  - result 節が抽象的な総括に寄る
  - condition 節が 1〜2 文の痩せた一般論で止まる
  - must-cover の自然反映より prompt-role の言い換えが先行する

### verdict
- rollback
  - `section_generator` で `user_instruction / anchor_terms` を強める案は keep しない
- reason
  - readability は改善せず、`contract_fit` がむしろ低下した
  - source evidence starvation を切ったあとでも、弱いのは generation prompt の語彙ではなく、`section intent -> usable fact selection` 境界のまま
- next narrow slice
  - owner 候補: `C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py` かその直後の section materialization 境界
  - 仮説: `change / condition` へ渡す fact が単文では足りず、usable fact pair / contrast が不足している

## 2026-04-06 追記（case_study discourse pair packing rollback）

### hypothesis
- `case_study` の読みにくさは `discourse_planner` で `change / condition` に渡す source grounding が単発 fact のまま薄いことが主因
- `usable fact pair` を `discourse_planner.py` owner だけで追加すれば、`section_generator` を触らずに後半 2 節の prose を改善できる

### owner
- `C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py`

### backup
- `C:\tetie\notecode\backups\2026-04-06_case_study_pair_packing_pre`

### attempted diff
- attempt 1
  - `change / condition` へ最大 2 本の complementary source grounding を route-local に追加
  - `change` は `before/process`、`condition` は `process/change` を補完候補にした
- attempt 2
  - mixed sentence を sentence 粒度に分割し、`process + effect` の混在 fact を `change` 側へ寄せる repair を追加

### owner-local tests
- attempt 1 keep 前
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st05ab7c or st05ab7d or st05ab7e or st05ab7f" -q`
    - `4 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_natural_blog_core.py -k "case_study_discourse_plan_reserves_change_and_condition_sections or case_study_condition_section_prefers_condition_terms_over_cycled_must_cover" -q`
    - `2 passed`
- attempt 2 keep 前
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st05ab7c or st05ab7d or st05ab7e or st05ab7f or st05ab7g" -q`
    - `5 passed`
  - 同 `natural_blog_core` subset
    - `2 passed`

### shared checks
- attempt 1 keep 前
  - `65 / 14 / 83 passed`
- attempt 2 keep 前
  - `65 / 14 / 83 passed`
- rollback 後
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `65 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `14 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `83 passed`

### live rerun artifacts
- attempt 1
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260406-casepair-rerun1`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260406-casepair-rerun2`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260406-casepair-rerun3`
- attempt 2
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260406-casepair2-rerun1`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260406-casepair2-rerun2`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-validation-20260406-casepair2-rerun3`

### live reading
- attempt 1
  - `case_study`: `3/3 short_gate pass`, `rubric mean 6.33` (`7 / 5 / 7`)
  - `source_trace_coverage`: `1.0 / 0.6667 / 1.0`
  - pair packing 自体は入るが、`change` が process-led な source を拾い、result prose が説明寄りに戻る run が残った
- attempt 2
  - `case_study`: `3/3 short_gate pass`, `rubric mean 5.33` (`7 / 5 / 4`)
  - sentence split を入れると run variance がむしろ増え、rerun3 で readability が悪化

### verdict
- rollback
  - `discourse_planner.py` の `pair packing` / `sentence split` は keep しない
- reason
  - owner-local / shared checks は通るが、live 3 rerun で acceptance が安定しない
  - `change` の改善よりも source の再配置説明が前に立ち、自然文の改善へつながらない
  - sentence 粒度 split は `fact selection` の改善ではなく source fragmentation を増やし、かえって揺れを大きくした
- next narrow slice
  - owner 候補: `C:\tetie\notecode\note\newalgorithm_pipeline\section materialization` 境界か `pipeline.py` の case_study local realization boundary
  - 仮説: weak point は upstream selection だけでなく、selected fact を result/condition prose に変換する local realization 制御
