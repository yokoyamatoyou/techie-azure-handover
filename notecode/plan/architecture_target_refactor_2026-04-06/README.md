# architecture_target_refactor_2026-04-06 README

## Objective

- deepresearch `(3)(4)(5)` と Web 一次情報を整理し、`notecode` 次期 mainline の target architecture を package として固定する
- current success path を壊さずに、`keep core, refactor boundaries` を実行可能な phase map に落とす
- Phase 01-06 の narrow implementation を完了済み package として保持し、closeout / handoff の入口を固定する

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md`
4. `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\TASK.md`
5. `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md`
6. `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md`
7. `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md`
8. `C:\tetie\notecode\ALGORITHM.md`
9. `C:\tetie\WORKLOG.md`

## Source Of Truth

- current runtime baseline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- completed refactor package:
  - `C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\`
- deepresearch inputs:
  - `C:\tetie\notecode\research\新しいフォルダー (3)\`
  - `C:\tetie\notecode\research\新しいフォルダー (4)\`
  - `C:\tetie\notecode\research\新しいフォルダー (5)\`

## Current Decision

- verdict:
  - `hybrid target architecture`
- repo decision:
  - `keep core, refactor boundaries`
- not adopted:
  - `keep as-is`
  - `replace architecture`

## Package State

- package status:
  - completed
- freeze status:
  - frozen
- archive readiness:
  - archive-ready
- implementation completion:
  - Phase 01 Canonical Plan State
  - Phase 02 Attributed Fact Slots
  - Phase 03 Section State Promotion
  - Phase 04 Route-Gated Section-First Mainline
  - Phase 05 Constrained Micro-Revision
  - Phase 06 Wrapper Demotion
- closeout decision:
  - package closeout を正規タスクとする
  - final visual loop はこの package の completion gate には含めない
  - 実生成物 review が必要な場合は current mainline artifact review として別タスクで扱う
- next action:
  - handoff / freeze completed
  - 次に進む場合は新 package か明示 artifact review task を切る
- reuse mode:
  - `completed architecture decision package` として参照する
  - completed phase の implementation は reopen しない
  - この package 自体へ新 phase や follow-up implementation を継ぎ足さない

## Why

- 現行 mainline の実体は planner-driven 本流ではなく、`single-pass writer + wrapper/reviser` に寄っている
- `discourse_planner.py` と `section_generator.py` には再利用価値の高い core がある
- 長文品質の支配 state が canonical に一本化されておらず、planner / writer / repair が複数化している
- Web 一次情報は、`canonical plan state + local section state + constrained revision` の方向を支持している
- 全面刷新は current success path と rollback discipline に反する

## Target Architecture

### Keep

- `DiscourseSection` を中心にした section contract の考え方
- route-aware source grounding の分類と節配賦
- section-first writer の逐次生成器
- diagnostics / guard / quality check の validator 面

### Refactor

- canonical plan state を 1 本に正規化する
- `source_grounding_items` を attributed fact slots として扱う
- `previous_summary` 依存を弱め、section ledger / remaining obligations を planner-owned state へ引き上げる
- revision を hidden writer ではなく constrained micro-revision に縮退させる
- `newalgorithm_pipeline` と `simple_note_pipeline` の役割境界を再定義する

### Replace

- default quality spine としての `single-pass + rescue chain`
- compatibility wrapper が恒久本体になる前提
- prompt-only strengthening で押し切る方針

## Non-Goals

- 現 package で runtime を直接作り替えること
- closeout 以外で新しい implementation phase を足すこと
- `gptpro_refactor_2026-04-01` を reopen して履歴を混ぜること
- `section_generator.py` prompt 強化の failed hypothesis を再投入すること
- proposition density を hard gate にすること
- Anthropic emotion 論文を architecture 主根拠にすること

## External References

- Plan-and-Write:
  - https://ojs.aaai.org/index.php/AAAI/article/view/4726
- Re3:
  - https://openreview.net/forum?id=C8Vo6sUWaN
- PlotMachines:
  - https://arxiv.org/abs/2004.14967
- LongWriter:
  - https://arxiv.org/abs/2408.07055
- CogWriter:
  - https://arxiv.org/abs/2502.12568
- WriteHERE:
  - https://aclanthology.org/2025.emnlp-main.1254/
- Attribute First, then Generate:
  - https://aclanthology.org/2024.acl-long.182/
- Self-Refine:
  - https://openreview.net/forum?id=S37hOerQLB
- Self-correction limits:
  - https://aclanthology.org/2024.tacl-1.78/
  - https://openreview.net/forum?id=a8U6Pju1h6
- Anthropic emotion concepts:
  - https://www.anthropic.com/research/emotion-concepts-function
