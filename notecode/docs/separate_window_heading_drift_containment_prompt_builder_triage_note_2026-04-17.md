# separate window heading drift containment prompt builder triage note 2026-04-17

## Position

- この文書は `HEADING_DRIFT_CONTAINMENT_FIRST` line の `prompt_builder.py` owner-local triage note である
- current source-of-truth update ではない
- implementation 実行結果ではない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ参照ルールファイル
- 実施範囲
- `prompt_builder.py` 内で見た candidate levers
- first lever の結論
- narrow hypothesis
- second lever を今やらない理由
- prompt accretion risk の評価
- next prompt type が implementation prompt でよいか
- 新しい指示ウインドウ向け carry-back summary
- non-updates

## 読んだ参照ルールファイル

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\docs\separate_window_instruction_handoff_heading_drift_containment_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_heading_drift_containment_management_planning_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_containment_prompt_builder_triage_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_containment_prompt_builder_triage_for_new_instruction_window_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_visible_smoke_after_rollback_note_2026-04-17.md`
- `C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\summary.json`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

## 実施範囲

- docs / logs / code reference を読み、`prompt_builder.py` の first lever を 1 つに絞ることだけを行った
- `pipeline.py` の compact-plan scaffold / repair dispatch / acceptance reopen は判断対象から外した
- `quality_guard.py` の trigger / issue classification reopen は判断対象から外した
- live rerun / code edit / test edit には進んでいない

## `prompt_builder.py` 内で見た candidate levers

### 1. `TITLE_LEAD_HEADING_CONTRACT_FIRST`

- `build_generation_prompt()` の `HARD_CONTRACT` と `STRUCTURE` には generic な本文制約はあるが、title / lead / first heading / first-section role を同一 frame に縛る contract はまだ薄い
- 該当箇所:
  - `prompt_builder.py:939-997`
  - `prompt_builder.py:1775-1847`
- `build_article_style_lines()` の title / lead guidance は non-company-intro では `温度感タイトル` / `温度感導入` として出るが、`company_introduction` ではそのままは出していない
- 該当箇所:
  - `prompt_builder.py:281-346`
- visible failure が
  - title drift
  - lead drift
  - heading wording / sequence drift
  - company intro first heading の history-first reanchor
  にまたがっているため、最も coverage が広い

### 2. `COMPANY_INTRO_FRAME_REUSE_FIRST`

- blank company intro 向け current-business-first line はすでに `_preflight_company_intro_generation_blocks()` で入っている
- 該当箇所:
  - `prompt_builder.py:836-903`
- ただし発火条件は `topic` / `prompt_raw` blank のときに限られている
- 該当箇所:
  - `prompt_builder.py:1974-1982`
- 会社紹介 guard には直接効きやすいが、explanatory 側の title / lead drift には効かない

### 3. `SECTION_SHADOW_EMISSION_FIRST`

- company intro 向け shadow summary 自体は組み立てられるが、generation prompt では `company_introduction` のとき `[SECTION_SHADOW]` を明示的に出さない
- 該当箇所:
  - `prompt_builder.py:1516-1588`
  - `prompt_builder.py:1792-1806`
- 既存 test でも omission が keep されている
- 該当箇所:
  - `test_simple_note_pipeline.py:1971-2027`
- narrow ではあるが、section-level frame を戻すぶん prompt accretion と keep-state 逆行の risk が高い

### 4. `STRUCTURE_ONLY_FIRST`

- `STRUCTURE` には heading count / heading progress / company intro structure language がすでにある
- 該当箇所:
  - `prompt_builder.py:729-738`
  - `prompt_builder.py:766-790`
  - `prompt_builder.py:955-978`
- ただしこれだけだと title / lead drift を owner-local に吸えず、current visible failure の main surface を取りこぼす

## first lever の結論

- first lever:
  - `TITLE_LEAD_HEADING_CONTRACT_FIRST`

理由:

- 4 candidate の中で、title / lead / heading wording / heading sequence / first-section role を 1 file / 1 diff で同時に触れるのはこれだけである
- `COMPANY_INTRO_FRAME_REUSE_FIRST` は company intro にしか効かず、V1 / V2 explanatory drift を取りこぼす
- `SECTION_SHADOW_EMISSION_FIRST` は keep 済み omission をひっくり返す reopen に近く、prompt accretion risk が高い
- `STRUCTURE_ONLY_FIRST` は narrow だが title / lead drift に届かない

## narrow hypothesis

- `prompt_builder.py` の generation prompt assembly で、title / lead / first heading / first-section role を 1 つの article-frame contract として短く固定すれば、repair acceptance reopen なしで initial draft の drift を先に抑えられる
- first implementation は `build_generation_blocks()` と `build_generation_prompt()` の generation-side contract line に閉じる
- first implementation では
  - `pipeline.py` を触らない
  - `quality_guard.py` を触らない
  - `[SECTION_SHADOW]` の company intro 再導入をやらない
  - title / lead / heading / first-section anchor の contract cluster だけを追加・強化する

## second lever を今やらない理由

- second lever backlog:
  - `COMPANY_INTRO_FRAME_REUSE_FIRST`

理由:

- blank company intro current-first line 自体はすでに keep されており、`test_blank_company_intro_generation_prompt_locks_first_section_to_current_business()` でも固定されている
- 該当箇所:
  - `prompt_builder.py:836-903`
  - `test_simple_note_pipeline.py:3570-3603`
- 先にこれを強めると company intro guard には寄るが、explanatory の title / lead / heading drift を残したままになる
- したがって first step は cross-case に効く contract cluster を先に入れ、company intro の history-first residual が残る場合だけ second lever として使うのがよい

## prompt accretion risk の評価

- `TITLE_LEAD_HEADING_CONTRACT_FIRST`
  - `low-medium`
  - 新 block 追加ではなく existing `HARD_CONTRACT` / `STRUCTURE` に短い contract line を足すだけで済む
- `COMPANY_INTRO_FRAME_REUSE_FIRST`
  - `low`
  - ただし coverage が narrow すぎる
- `SECTION_SHADOW_EMISSION_FIRST`
  - `high`
  - section-level lines の再導入で token と責務が増え、既存 keep test に逆行する
- `STRUCTURE_ONLY_FIRST`
  - `low`
  - ただし containment value が不足する

## next prompt type が implementation prompt でよいか

- verdict:
  - `yes`
- exact read:
  - owner-local triage はここで十分に閉じた
  - next は `prompt_builder.py` owner の implementation prompt でよい
  - implementation scope は `TITLE_LEAD_HEADING_CONTRACT_FIRST` だけに固定する
  - second lever 以上は持ち込まない

## 新しい指示ウインドウ向け carry-back summary

- current redirect line:
  - `HEADING_DRIFT_CONTAINMENT_FIRST`
- first owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- first lever:
  - `TITLE_LEAD_HEADING_CONTRACT_FIRST`
- narrow hypothesis:
  - generation prompt の `HARD_CONTRACT` / `STRUCTURE` に title / lead / first heading / first-section role を同一 frame に縛る短い contract cluster を追加し、initial draft の frame drift を先に containment する
- second lever backlog:
  - `COMPANY_INTRO_FRAME_REUSE_FIRST`
- do not first:
  - `quality_guard.py` first
  - repair acceptance reopen
  - `SECTION_SHADOW` company intro 再導入
  - `sentence-final monotony` continuation
- next prompt type:
  - `prompt_builder.py` owner の implementation prompt
- non-update carry-back:
  - production code / tests / AGENTS / WORKLOG / current package docs は更新していない

## non-updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない
