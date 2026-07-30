# PROGRESS

## Status

Phase 00 docs-only diagnosis package created.

Phase 01 owner-local implementation attempt completed on `2026-04-27`.

- Product owner touched:
  - `C:\tetie\notecode\note\current_mainline_persona_trial.py`
- Test/docs touched:
  - `C:\tetie\notecode\note\tests\test_current_mainline_runner.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
  - `C:\tetie\notecode\ALGORITHM.md`
- UI server was not restarted for this attempt; runner validation was used.
- Result:
  - `persona_trial.late_return_target` no longer points to consultation/pre-contact framing for `branding/company_introduction`.
  - The visible generation gate is not closed because reconstructed prompt still contains consultation-entry steering from `prompt_builder.py` / title surface.
  - Do not widen this phase to `prompt_builder.py` or `title_strategy.py` without a new owner decision.

Phase 02 prompt/title surface implementation attempt completed on `2026-04-27`.

- Product owner touched:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\title_strategy.py`
- Test/docs touched:
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
  - `C:\tetie\notecode\plan\current_mainline_company_intro_persona_packet_diagnosis_2026-04-27\PROGRESS.md`
  - `C:\tetie\WORKLOG.md`
- Result:
  - `company_introduction` の title pattern は `現在事業 + 支援範囲 + 相談前判断` から `事業内容 + 扱う領域 + 会社の特徴` へ置換。
  - generation / repair prompt surface の company-introduction default は `私たちの事業内容` / `扱っている製品・サービス` / `対応範囲` / `事業の特徴` / `会社としての姿勢` へ寄せた。
  - Sanin 4 URL 実生成では `runtime_reason_code=OK`、bodyあり、source_count=4、URL保持、`blocked_output_redacted=false` の成功 run は複数確認。
  - ただし同一条件の反復で `この会社は` / `相談の入口` / `欠かせない` が再発したため、prompt_builder/title surface だけでは完全 close できない。
  - 今回の owner 境界では guard / pipeline / hidden late validation / repair acceptance へ広げず停止。

## Phase 01 Implementation Attempt

### Changed

- `company_intro_operational` family now returns to:
  - current business
  - products / services handled
  - support scope
  - company posture
  - source-backed background
- company-introduction generation guard no longer treats `customer_situation_or_entry_point` as the reader-friction default.
- company-introduction diagnostic repair guard no longer says `現在事業・相談の入口・支援範囲・相談前判断`.
- Non-target `branding` and `comparative_review` late-return targets were kept.

### Focused Checks

- `C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile note\current_mainline_persona_trial.py note\tests\test_current_mainline_runner.py note\tests\test_simple_note_pipeline.py`
  - passed
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py -k "persona_trial or company_intro" -q`
  - `13 passed, 65 deselected`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "company_intro or company_introduction or generation_prompt" -q`
  - `113 passed, 132 deselected`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py -k "announcement or comparative_review" -q`
  - `3 passed, 75 deselected`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "announcement or comparative_review" -q`
  - `14 passed, 231 deselected`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
  - `22 passed`

### Runner Validation

Sanin 4 URL runner validation:

- URLs:
  - `https://www.sanin-sanso.co.jp/`
  - `https://www.sanin-sanso.co.jp/company/info/`
  - `https://www.sanin-sanso.co.jp/company/history/`
  - `https://www.sanin-sanso.co.jp/home/price/`
- Runner result after second owner-local fix:
  - `2/4` runs returned `runtime_reason_code=OK`
  - `2/4` runs returned `SYS_PIPELINE_FAILURE` with `Company introduction hard source contract trigger remained after repair`
  - both OK runs had `source_count=4`, URL retention, non-empty body, `blocked_output_redacted=false`
  - internal term leakage was not observed in the visible excerpts
  - `persona_trial.late_return_target` was `最後は私たちの事業内容、扱う領域、対応範囲、会社としての姿勢へ戻す。`
- Visible residual:
  - OK output still organized around `相談範囲`, `相談先`, or `相談の入口`
  - one OK run had exact forbidden hit `相談の入口`
  - another OK run avoided exact `相談の入口` but still read as consultation-surface framing

### Stop Judgment

This phase improved the owner-local late-return source, but did not close the visible symptom.

Prompt reconstruction after the patch still contains:

- `相談前`: `2`
- `相談入口`: `1`
- `導入`: `7`
- `問い合わせ後`: `2`

Matched prompt surface includes:

- `何をしている会社か・支援範囲・相談入口`
- `現在事業、支援範囲、相談前判断を説明する距離`
- `タイトル型: 現在事業 + 支援範囲 + 相談前判断`
- `問い合わせ後の流れ、導入手順、事前チェック`

Therefore `current_mainline_persona_trial.py` alone is insufficient for the visible closeout. The next owner should be a separate decision, most likely the company-introduction prompt/title surface inside `prompt_builder.py` and/or title strategy, not a continuation inside this phase.

## Phase 02 Prompt / Title Surface Attempt

### Changed

- `title_strategy.py`
  - `company_introduction` title strategy:
    - before: `現在事業 + 支援範囲 + 相談前判断`
    - after: `事業内容 + 扱う領域 + 会社の特徴`
- `prompt_builder.py`
  - company-introduction structure summary fallback:
    - before: `現在事業、支援範囲、相談前判断`
    - after: `私たちの事業内容、扱っている製品・サービス、対応範囲、会社としての姿勢`
  - reader script brief:
    - `何をしている会社か` / `相談入口` / `相談前判断` default frame を `私たちの事業内容` / `対応している領域` / `事業の特徴` へ置換。
  - company-introduction craft lines:
    - 手続きや利用条件は資料に明記がある場合だけ補助扱い。
    - 設備やサービスは利用手順ではなく事業内容と対応範囲として説明。
    - `欠かせない` 型の一般価値語を避け、source の事業内容・製品サービス・対応範囲の語で説明。
  - repair prompt guard:
    - `支援範囲 / 相談前判断` label を `対応範囲 / 補助情報` へ置換。

### Focused Checks

- `py_compile note\simple_note_pipeline\prompt_builder.py note\simple_note_pipeline\title_strategy.py note\tests\test_simple_note_pipeline.py note\tests\test_current_mainline_runner.py`
  - passed
- `pytest note\tests\test_simple_note_pipeline.py -k "company_intro or company_introduction or generation_prompt or title_strategy" -q`
  - `114 passed, 131 deselected`
- `pytest note\tests\test_current_mainline_runner.py -k "company_intro or company_introduction" -q`
  - `13 passed, 65 deselected`
- smoke:
  - `test_announcement_runtime_source_contract_adds_base_pattern_without_fixed_route`: passed
  - `test_comparative_prompt_keeps_craft_rules_without_persona_editor_or_trial_names`: passed

### Runner Validation

Artifact:

- `C:\tetie\notecode\logs\company_intro_prompt_title_surface_validation_20260427-222425\`

Sanin 4 URL runner validation:

- source URLs:
  - `https://www.sanin-sanso.co.jp/`
  - `https://www.sanin-sanso.co.jp/company/info/`
  - `https://www.sanin-sanso.co.jp/company/history/`
  - `https://www.sanin-sanso.co.jp/home/price/`
- outcome:
  - `OK` bodyあり runs: multiple
  - `source_count=4` and URL retention: confirmed on all saved runs
  - `blocked_output_redacted=false`: confirmed on saved success runs
  - internal term leakage: not observed
- visible improvement:
  - title / lead generally moved to `エネルギー供給`, `住まいづくり`, `事業`, `対応範囲`, `私たちの事業`
  - clean examples include run 5 / run 9 / run 12 with no exact forbidden hits in the saved checker
- residual:
  - run 11: `相談の入口` / `相談窓口` and `欠かせない`
  - run 13: `この会社は`
  - run 14: `相談の入口`
  - final-code rerun: run 15 was clean `OK`, run 16 was fail-closed `SYS_PIPELINE_FAILURE`
  - therefore prompt/title surface replacement alone is not stable enough for final closeout.

### Stop Judgment

This phase confirms that prompt/title wording was a real reinjection surface and that replacing it improves many outputs, but it does not fully prevent visible reintroduction under repeated runner generation.

Do not widen this phase to:

- `pipeline.py`
- source contract guard
- hidden late validation
- repair acceptance
- output guard
- threshold / repair count changes

Next owner must be a separate decision if full closeout is required.

## Investigated Logs

- `C:\tetie\notecode\logs\latest_ui_journey.json`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\latest_generation_output.txt`
- `C:\tetie\notecode\logs\latest_generation_quality_report.json`
- `C:\tetie\notecode\logs\app.log`
- `C:\tetie\notecode\logs\company_intro_naturalness_prompt_surface_20260427\`

Latest baseline:

- attempt: `gen-75fac897`
- source count: `4`
- fetch result: `success=4 failure=0`
- generation core: completed
- final outcome: success with quality warning
- semantic article key: `company_introduction`

## Unnatural Output Excerpts

- `ガス・電気・住まいを支える事業と、相談の入口が見える会社紹介`
- `## 相談の入口はどこにあるか`
- `案内の入口として見えやすいのは、ガスや電気に関する相談と、住まいづくりの相談です。`
- `規格を当てはめるより、暮らし方に合わせて考えたい人に向いた相談先だと受け取れます。`
- `支援範囲は、供給、販売、設計、施工、住まいの相談まで広がっています。`
- `まとめて相談しやすい形にしているのがこの会社の見え方です。`

## Likely Reinjection Route

The consultation framing is most likely injected before the first LLM generation:

- final output and rejected repair candidate both contain the same consultation-entry frame
- `formatter_applied=false`, so `output_formatter.py` did not create the latest visible wording
- hidden late validation did not trigger for the latest artifact
- prompt reconstruction still contains `相談前`, `相談入口`, `相談の入口`, `導入`, and `確認`
- `current_mainline_persona_trial.py` contains company-introduction defaults for `相談の入口`, `相談前判断`, and `最後は相談前に何を確認すると判断しやすいかへ戻す。`

The exact raw prompt is not persisted in the latest artifact, so prompt diagnosis uses persisted input contracts and non-mutating prompt reconstruction.

## Why `prompt_builder.py` Alone Is Insufficient

`prompt_builder.py` materializes upstream contract and persona direction. The rollback removed the failed prompt-surface patch, but the reconstructed prompt still contains consultation-entry terms because upstream persona/source-packet/title composition still supplies them.

The first implementation owner should therefore remove the default consultation/pre-contact steering at the persona-trial source, rather than adding another prompt-builder overlay.

## Cause Classification

- **A: contributing.** Source packet / slot naming maps official consultation source text into `customer_situation_or_entry_point`, then surfaces it as `相談入口`.
- **B: primary.** `persona_trial.late_return_target` and company-introduction persona guidance default to consultation/pre-contact framing.
- **C: unlikely.** Hidden late validation did not trigger or reintroduce wording in the latest artifact.
- **D: secondary.** `title_strategy.py` contributes `相談前判断` to prompt surface; `output_formatter.py` has risky fallback wording but was not applied.
- **E: secondary.** Repair/semantic trigger does not treat thin consultation bridge wording as a semantic issue; the optional repair fired for fingerprint flatness and was rejected.
- **F: confirmed symptom.** Prompt surface still contains consultation-entry terms after the prompt-builder rollback.

## Next Narrow Owner

Next owner: `C:\tetie\notecode\note\current_mainline_persona_trial.py`.

Next hypothesis: for company introduction, default persona guidance should organize around current business, service/product scope, support posture, and source-backed company facts. Consultation/pre-contact framing should not be the default late-return or heading direction when `pre_contact_decision` is missing.

## Phase 00 Not Implemented

- Product code changes: none.
- `prompt_builder.py` overlay: none.
- Repair count changes: none.
- Editing persona behavior changes: none.
- Threshold changes: none.
- Source contract broadening: none.
- UI validation run: none in this docs-only phase.
- Pytest run: none in this docs-only phase.

## WORKLOG / AGENTS

- `C:\tetie\WORKLOG.md` updated as a docs-only diagnosis entry.
- `AGENTS.md` update is not needed. This package is a diagnosis/handoff package, not a replacement for the current source-of-truth read order.
