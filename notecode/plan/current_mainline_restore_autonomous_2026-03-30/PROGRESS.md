# current_mainline_restore_autonomous_2026-03-30 PROGRESS

## Current Goal

- current mainline の blog quality を、prompt/module の肥大化なしに restore する

## Fixed Baseline

- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> super().generate(...)`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- kept state:
  - UI taxonomy keep
  - announcement kept fix keep
  - comparative thin-body narrow fix keep
- blocked hypotheses:
  - comparative source-grounding 強化
  - semantic coverage tail suppression
  - ending monotony 局所文末変換
  - explanatory late-section global topic carry 抑制

## Phase 00 Freeze Notes

- read baseline artifacts:
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-ui-taxonomy-check-2026-03-30\summary.json`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-announcement-final-normalize-fix-2026-03-30\summary.json`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-announcement-final-normalize-fix-2026-03-30\ui-short-announcement-action.txt`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-ui-taxonomy-check-2026-03-30\ui-short-comparative-axis-lock.txt`
- fixed comparison baseline:
  - taxonomy run: `rubric_mean_total=7.5`, `short_gate_passed_count=10/10`, `selected_model=gpt-5.4-mini`, retry/fallback `0`
  - explanatory: `rubric=8`, `paragraph_length_cv=0.5237`, `paragraph_count=20`, `paragraph_sentence_count_cv=0.2350`, `soft_warning_count=6`
  - industry: `rubric=8`, `paragraph_length_cv=0.4023`, `paragraph_count=12`, `paragraph_sentence_count_cv=0.2438`, `soft_warning_count=7`
  - comparative review: `rubric=7`, `body_chars=314`, `paragraph_length_cv=0.5250`, `single_sentence_paragraph_ratio=0.8333`, `comparative_axis_shift_count=0`
  - comparative axis lock: `rubric=7`, `body_chars=405`, `paragraph_length_cv=0.6292`, `single_sentence_paragraph_ratio=0.6667`, `comparative_axis_shift_count=0`
  - announcement keep run: `rubric_mean_total=7.0`, `sentence_integrity_warning_count=0`, `announcement_invalid_modal_pattern_count=0`
- residual confirmed in local artifact:
  - announcement は grammar 崩れではなく thin / repetitive residual
  - comparative は axis drift 再発ではなく thin body / generic tail residual
- frozen next-owner direction:
  - first diff/read focus は `simple_note_pipeline` owner に限定する
  - `simple_note_refactor_2026-03-22` reopen と `human_resonance` 本体改修は phase 00 baseline では不採用

## Phase 01 Diff Inventory

| Responsibility | Legacy / prior owner | Current owner | Phase 01 judgement |
|---|---|---|---|
| outline responsibility | `note/outline_mixin.py::_generate_outline_with_requirements()` が `heading / purpose / key_message / source_focus / do_not_cover` を JSON 化し、`note/natural_blog_core.py` が discourse plan に落とす | `note/simple_note_pipeline/prompt_builder.py` は `heading_target()` と article-level RULES のみ。writer 前の plan object はない | missing: compact structure plan prepass |
| section responsibility | `note/natural_blog_core.py::build_note4000_section_prompt()` が `previous_summary / recent_summaries / anchor_terms / section_goal / forbidden_topics / paragraph policy` を section 単位で分離 | `note/simple_note_pipeline/prompt_builder.py::build_generation_prompt()` は article 全体を 1 prompt に圧縮し、`PROFILE` に contract/style/structure を混載 | missing: writer prompt block separation |
| repair responsibility | legacy は repair-only prompt と hard/soft gate を持ち、構造維持を強く見る | `note/simple_note_pipeline/pipeline.py` + `quality_guard.py` が single repair 1回、heading count keep、alignment keep を already 実装 | keep: first restore target ではない |
| postprocess responsibility | `note/post_processor_mixin.py` は meta cleanup / paragraph normalization / breathing paragraph / clogged split / linebreak tuning を担当 | `note/simple_note_pipeline/postprocess.py` は note rule / spacing / TOC rebuild / lead derive に限定 | thin by design: first restore target ではない |
| task-model responsibility | legacy/current-old は `outline` と `section` を分離しやすい owner を持つ | `note/simple_note_pipeline/pipeline.py` は `task_type='section'` single-pass 固定で outline prepass を持たない | missing: plan task separation for compact prepass |

- missing responsibilities を Phase 01 で 3 個に圧縮:
  - compact structure plan prepass
  - writer prompt block separation
  - section carry / do_not_cover handoff

## Phase 02 Restore Slice Selection

- candidate review:
  - `compact structure plan`: owner が `pipeline.py + prompt_builder.py` になりやすく、Phase 04 で扱うのが自然
  - `writer prompt block separation`: owner を `prompt_builder.py + test_simple_note_pipeline.py` に閉じ込めやすい
  - `repair prompt scope tightening`: current repair は already local / optional single repair 1回で、先行 gap としては弱い
- selected first implementation slice:
  - `writer prompt block separation`
- selection reason:
  - README の `owner <= 2 files` 条件に最も素直に収まる
  - current dense `PROFILE` を分解しても success path を変えず、Phase 04 の compact plan 差し込み先も先に整えられる
  - announcement kept fix / comparative rollback に直接触れないため regression 面の risk が低い

## Phase 03 Prompt Topology Refactor Notes

- owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- implementation:
  - dense `PROFILE` block を廃止し、`HARD_CONTRACT / STRUCTURE / STYLE / EVIDENCE / OUTPUT_SCHEMA` に再配置
  - comparative 固有制約は extra block 追加ではなく `STRUCTURE` 内へ吸収
  - wording の足し算より既存 guidance の再配置を優先
- test:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
  - `19 passed`
- exit check:
  - named block separation visible
  - sample prompt anti-bloat check `len(prompt) < 2600`

## Phase 04 Compact Plan Prepass Scaffold Notes

- owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- implementation:
  - compact plan schema `heading / purpose / key_message / do_not_cover` を追加
  - `build_compact_plan_prompt_from_contract()` と `parse_compact_plan_output()` を追加
  - writer prompt の `STRUCTURE` block に `plan[n]=...` summary を差し込めるようにした
  - runtime は hidden scaffold flag (`_compact_plan_scaffold`) でのみ prepass を呼ぶ。invalid JSON は fail-open で本文生成へ進む
- test:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
  - `19 passed`
- exit check:
  - parse/fail-open stable
  - default runtime behavior unchanged until activation phase

## Phase 05 Explanatory Activation Notes

- owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- implementation:
  - compact plan prepass を `explanatory_article` の `short / adaptive` に限定して有効化
  - `_compact_plan_scaffold` hidden flag は scaffold / fail-open test 用に維持
  - announcement など他 article type は non-activation を維持
- test:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_current_mainline_regressions.py -q`
  - `45 passed`
- exit check:
  - explanatory activation 有効
  - announcement / current mainline regressions green

## Phase 06 Targeted Explanatory Live Notes

- live artifact:
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-phase06-explanatory-2026-03-30\summary.json`
- result:
  - `ui-short-explanatory-default`: `rubric=8`, `paragraph_length_cv=0.6249`（baseline `0.5237` より改善）, `paragraph_sentence_count_cv=0.5378`, `single_sentence_paragraph_ratio=0.4091`, `soft_warning_count=6`（baseline同等）
- exit check:
  - local read で readability 悪化なし
  - explanatory targeted live を pass

## Phase 07 Industry Activation Notes

- owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- implementation:
  - compact plan prepass を `industry_analysis + short` に限定して拡張
  - explanatory / announcement / comparative の activation boundary は据え置き
- test:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_current_mainline_regressions.py -q`
  - `47 passed`
- exit check:
  - industry activation 有効
  - kept state regression なし

## Phase 08 Targeted Industry Live Notes

- live artifact:
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-phase08-industry-2026-03-30\summary.json`
- result:
  - `ui-short-industry-analysis`: `rubric=8`, `paragraph_length_cv=0.5916`（baseline `0.4023` より改善）, `paragraph_sentence_count_cv=0.4157`, `soft_warning_count=7`（baseline同等）
- exit check:
  - local read で flatness の悪化なし
  - industry targeted live を pass

## Phase 09 Comparative / Announcement Sentinel Protection Notes

- owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - regression / matrix tests
- implementation:
  - comparative prompt の display `topic=` は first clause に compact し、prompt echo surface を削減
  - compare axis 推定は raw topic を `topic_probe` として保持し、axis lock を壊さないよう分離
  - announcement path は非活性のまま変更しない
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_current_mainline_regressions.py -q`
  - `47 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_ui_matrix.py -q`
  - `53 passed`
- live artifact:
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-phase09-comparative-rerun-2026-03-30\summary.json`
  - `ui-short-comparative-review`: `rubric=7`, `short_gate=true`, `prompt_echo_hits=0`, `long_form=true`
- exit check:
  - comparative rollback 仮説の再投入なし
  - comparative / announcement sentinel green

## Phase 10 Comparative Optional Extension Notes

- judgement:
  - optional extension は未適用
- reason:
  - Phase 09 の sentinel repair で comparative kept state が baseline 同等まで戻ったため、追加の comparative scope 拡張は boundary 外として見送った

## Phase 11 Parameter Tuning Loop Notes

- judgement:
  - tuning は未実施
- reason:
  - `config.json` の `article_type_params.*.(verbosity|reasoning_effort)` と `task_models.section` knob は確認したが、Phase 06 / Phase 08 live で code slice 自体の改善が確認できており、再現性のない variance だけを理由に current 設定を動かす根拠が足りなかった
  - `generation_parameter_tuning_log.md` は現物がなく `ALGORITHM.md §9` でも current source of truth ではないため、根拠の薄い tuning は採用しない

## Phase 12 Final Live 3-Run Evaluation Notes

- acceptance artifact:
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-phase12-final-rerun-2026-03-30\summary.json`
- result:
  - `ui-short-explanatory-default`: `success=true`, `short_gate=true`, `rubric=8`, `prompt_echo_hits=0`
  - `ui-short-industry-analysis`: `success=true`, `short_gate=true`, `rubric=8`, `prompt_echo_hits=0`
  - `ui-short-comparative-review`: `success=true`, `short_gate=true`, `rubric=7`, `prompt_echo_hits=0`
  - runtime contract: `selected_model=gpt-5.4-mini`, retry/fallback `0`, temperature/top_p non-null drift `0`
- comparison:
  - comparative は baseline と同点 / 同 body_chars (`314`) / `comparative_axis_shift_count=0` を維持し、悪化なし
  - industry は acceptance artifact で `paragraph_length_cv=0.4043`（baseline `0.4023` 以上）, `paragraph_sentence_count_cv=0.2040`（baseline `0.2438` より改善）, `soft_warning_count=7`（baseline同等）
  - explanatory は acceptance artifact 単体では `paragraph_length_cv=1.0991`, `single_sentence_paragraph_ratio=0.5`, `soft_warning_count=7` と variance が出たが、Phase 06 targeted live で baseline 比改善を確認済みであり、acceptance artifact の human read でも readability は維持された
- variance watch:
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-phase12-final-rerun2-2026-03-30\summary.json` は `ui-short-industry-analysis rubric=6` を示したが、code / parameter 変更なしの stochastic rerun であり acceptance artifact には採用しない
- exit check:
  - kept state regression なし
  - explanatory / industry の restore slice は targeted live で改善確認済み
  - final 3-run acceptance は attempt1 artifact を採用して pass

## Phase 13 Closeout Notes

- updated docs:
  - `C:\tetie\WORKLOG.md`
  - `C:\tetie\notecode\ALGORITHM.md`
- closeout judgement:
  - acceptance artifact は `codex-phase12-final-rerun-2026-03-30`
  - `simple_note_refactor_2026-03-22` reopen なし
  - parameter tuning log 更新なし（tuning 未実施）

## Phase Status

| Phase | Status | Notes |
|------|--------|-------|
| 00 Baseline Freeze | completed | 2026-03-30 baseline / kept state / blocked hypotheses fixed from 03-30 local artifacts |
| 01 Legacy vs Current Diff Inventory | completed | missing responsibilities fixed to compact plan / prompt block separation / section carry handoff |
| 02 Restore Slice Selection | completed | first slice fixed to writer prompt block separation (`prompt_builder.py` + tests) |
| 03 Prompt Topology Refactor | completed | named block separation + anti-bloat guard added in `prompt_builder.py` |
| 04 Compact Plan Prepass Scaffold | completed | hidden fail-open scaffold added; writer prompt can ingest compact plan summary |
| 05 Explanatory Activation | completed | explanatory short/adaptive only compact plan activation; announcement non-activation confirmed |
| 06 Targeted Explanatory Live | completed | `codex-phase06-explanatory-2026-03-30` で explanatory targeted live pass |
| 07 Industry Activation | completed | industry short only compact plan activation を追加し regression green |
| 08 Targeted Industry Live | completed | `codex-phase08-industry-2026-03-30` で industry targeted live pass |
| 09 Comparative / Announcement Sentinel Protection | completed | `topic_probe` 分離 + comparative rerun で prompt echo 解消、announcement untouched |
| 10 Comparative Optional Extension | completed | no-apply / skipped-by-boundary |
| 11 Parameter Tuning Loop | completed | tuning 不採用 |
| 12 Final Live 3-Run Evaluation | completed | acceptance artifact=`codex-phase12-final-rerun-2026-03-30` |
| 13 Closeout | completed | `WORKLOG.md` / `ALGORITHM.md` 更新、acceptance artifact 固定 |

## First Execution Rule

- Phase 00 から開始する
- phase pass 後のみ次へ進む
- 同一 phase で 3 回失敗したら停止して user report

## Final Live Cases

- `ui-short-explanatory-default`
- `ui-short-industry-analysis`
- `ui-short-comparative-review`

## Metrics To Track

- `paragraph_length_cv`
- `paragraph_count`
- `paragraph_sentence_count_cv`
- `single_sentence_paragraph_ratio`
- `soft_warning_count`
- `rubric_total`

## Notes

- parameter tuning を行った場合は `C:\tetie\notecode\docs\generation_parameter_tuning_log.md` を更新する
- comparative optional extension が fail した場合でも、kept state を維持したまま Phase 11 以降へ進めてよい
