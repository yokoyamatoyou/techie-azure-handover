# Naturalness Recovery Attempt Log

## Scope

- latest log baseline: `gen-b1732c2d` (`2026-04-10 21:08:24`)
- route: `branding` / `company_introduction`
- writer: `simple_note_pipeline`
- guardrail: root-cause fixes only
- rollback baseline:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\attempt_snapshots\input_contract_attempt00_baseline_2026-04-10.py`

## Baseline Symptoms

- visible output reads like a generic brochure
- narrator perspective is weak or ambiguous
- `topic=未指定` in rebuilt writer prompt
- `narrative_axis` and `knowledge_lenses` are empty in contract
- `source_grounding_items` contains broken LP fragment: `創業社長でやってきたが`
- latest soft warnings:
  - `ending:bucket_monotony`
  - `ai:paragraph_variation`
  - `legal:unverified_legal_citation`
  - `omission:heading_reanchor`

## Attempt Ledger

| Attempt | Owner Scope | Hypothesis | Change | Verification | Result | Rollback |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | `note/newalgorithm_pipeline/input_contract.py` | company introduction loses narrative/topic backbone before writer prompt; blank prompt falls to `topic=未指定` | blank-prompt company intro で source-backed `topic_statement` を導出し、fragmentary source fact を filter | `note\tests\test_newalgorithm_phase01_contract.py -k "pr12" -q`; replay `attempt01_company_intro_replay.json` | keep: `heading_reanchor_miss_count 2 -> 1`, `omission_ambiguity_score 0.5 -> 0.25` | no |
| 02 | `note/simple_note_pipeline/prompt_builder.py` | fixed company-intro progression が must-cover を無視して marketing template を強めている | dynamic company-intro progression を追加 | `note\tests\test_simple_note_pipeline.py -q`; replay `attempt02_company_intro_replay.json` | rollback: `ending_bucket_max_run 10 -> 25` まで悪化 | yes |
| 03 | `note/current_mainline_runner.py` | replay / regenerate が prior resolved contract を再利用し、最新 resolve が効いていない | 再生成時に derived fields を剥がして `resolve_input_contract()` を必ず再実行 | `note\tests\test_current_mainline_runner.py -q`; replay `attempt03_company_intro_replay.json` | keep: stale `source_grounding_items` / `_shadow_spec_inputs` の持ち回り停止 | no |
| 04 | `note/simple_note_pipeline/prompt_builder.py` | `[SECTION_SHADOW]` が全節へ同じ focus/support を打ち、compact plan の節差を潰している | company-intro だけ `SECTION_SHADOW` を slim 化 | `note\tests\test_simple_note_pipeline.py -q`; replay `attempt04_company_intro_replay.json` | keep as intermediate: `ai_index_score 0.3461 -> 0.2969` だが omission は悪化 | no |
| 05 | `note/simple_note_pipeline/pipeline.py` | blank-prompt company-intro でも compact-plan scaffold が自動発火し、simple prompt より重い route に入っている | blank `prompt_raw/topic` の company-intro では compact plan を無効化し single generation に戻す | `note\tests\test_simple_note_pipeline.py note\tests\test_current_mainline_runner.py -q`; replay `attempt05_company_intro_replay.json` | keep: LLM calls `3 -> 2`; `heading_reanchor_miss_count 0`; `omission_ambiguity_score 0.0`; `ai_index_score 0.2308` | no |
| 06 | `note/simple_note_pipeline/prompt_builder.py` | compact plan を切っても company-intro writer prompt に `導入時重視点` の固定進行が残る | company-intro の structure / heading progress を must-cover driven に差し替え | `note\tests\test_simple_note_pipeline.py note\tests\test_current_mainline_runner.py -q`; replay `attempt06_company_intro_replay.json` | keep: `ending_bucket_max_run 14 -> 10`, `heading_reanchor_miss_count 0`, `omission_ambiguity_score 0.0` | no |

## Current Keep State

- retry-path keep:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - regenerate 時に derived contract fields を剥がして再 resolve する
- writer-route keep:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - blank-prompt `branding/company_introduction` では compact plan scaffold を起動しない
- prompt-surface keep:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - company-intro の `SECTION_SHADOW` を slim 化
  - company-intro の structure / heading progress を `must_cover` 基準へ寄せる
- contract keep:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
  - blank-prompt company intro の source-backed topic fallback を保持

## Latest Best Replay

- file:
  - `C:\tetie\notecode\logs\attempt06_company_intro_replay.json`
  - `C:\tetie\notecode\logs\attempt06_company_intro_replay.txt`
- summary:
  - title: `顧問弁護士を探している会社へ。吉野モア法律事務所が大切にしていること`
  - `ai_index_score = 0.2439`
  - `ending_bucket_max_run = 10`
  - `heading_reanchor_miss_count = 0`
  - `omission_ambiguity_score = 0.0`
  - LLM calls: `section -> section`
